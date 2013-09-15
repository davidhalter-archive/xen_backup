#!/usr/bin/python
"""
The export/import commands are pretty simple, just an easier interface than
``xe vm-import`` and ``xe vm-export``. The ``nfs-export-all`` option is pretty
powerful, exports all the current vms to an nfs device (mount syntax).

Usage:
  backup.py list
  backup.py export [-d=<directory>] --uuid=<uuid>
  backup.py export [-d=<directory>] [<search-term>...]
  backup.py search [<search-term>...]
  backup.py import <filename>
  backup.py nfs-export-all <device> <folder> [--delete-old]
  backup.py (-h | --help)

Options:
  -h, --help                Show this screen. 
  -d=<directory>, --dir     Directory path.
  --delete-old              Delete old files that are in the nfs directory
"""

import subprocess
import os
import time

from docopt import docopt


class CalledProcessError(Exception):
    """This exception is raised when a process run by check_call() or
    check_output() returns a non-zero exit status.
    The exit status will be stored in the returncode attribute;
    check_output() will also store the output in the output attribute.
    """
    def __init__(self, returncode, cmd, output=None):
        self.returncode = returncode
        self.cmd = cmd
        self.output = output

    def __str__(self):
        return "Command '%s' returned non-zero exit status %d" % (self.cmd, self.returncode)


def check_output(command, shell=False):
    p = subprocess.Popen(command, stdout=subprocess.PIPE, shell=shell)
    output, unused_err = p.communicate()               
    retcode = p.poll()                                 
    if retcode:                                              
        raise CalledProcessError(retcode, command, output=output)
    return output                                            


class VM(object):
    def __init__(self, uuid, name, status):
        self.uuid = uuid
        self.name = name
        self.status = status

    def __str__(self):
        return '%s - %s (%s)' % (self.uuid, self.name, self.status)

    def export(self, directory_name=None):
        start = time.time()
        timestamp = time.strftime("%Y-%m-%d_%H-%M-%S", time.gmtime())

        file_name = '%s %s.xva' % (timestamp, self.name)
        if directory_name is not None:
            file_name = os.path.join(directory_name, file_name)

        # create a snapshot
        snapshot_uuid = check_output(['xe', 'vm-snapshot', 'uuid=' + self.uuid,
                                      'new-name-label=backup-' + self.name]).strip()

        # change some params so that the snapshot can be exported
        cmd = "xe template-param-set is-a-template=false ha-always-run=false uuid=" + snapshot_uuid
        check_output(cmd, shell=True)

        # export snapshot
        cmd = 'xe vm-export vm=%s filename="%s" --compress' % (snapshot_uuid, file_name)
        check_output(['xe', 'vm-export', 'vm=' + snapshot_uuid, 
                      'filename=' + file_name, '--compress'])

        # remove old snapshot again
        cmd = "xe vm-uninstall uuid=%s force=true" % snapshot_uuid 
        check_output(cmd, shell=True)
        print('Exported VM "%s" in %s seconds.' % (self.name, time.time() - start))


def get_backup_vms():
    cmd = "xe vm-list is-control-domain=false is-a-snapshot=false"
    output = check_output(cmd, shell=True)

    result = []
    for vm in output.split("\n\n\n"):
        lines = vm.splitlines()
        if lines:
            uuid = lines[0].split(":")[1][1:]
            name = lines[1].split(":")[1][1:]
            status = lines[2].split(":")[1][1:]
            result.append(VM(uuid, name, status))
    return result


def nfs_export_all(nfs_path, directory, delete_old):
    if not os.path.exists(directory):
        os.makedirs(directory)

    try:
        check_output(['mountpoint', '-q', directory])
    except CalledProcessError:
        # if it's not a mountpoint yet
        check_output(['mount', nfs_path, directory])

    old_files = os.listdir(directory)

    for vm in get_backup_vms():
        vm.export(directory)
    
    if delete_old:
        for f in old_files:
            os.remove(os.path.join(directory, f))
    check_output(['umount', directory])


def print_vms(vms):
    if not vms:
        print('No VMs found.')
    for vm in vms:
        print(vm)


def search_by_names(names):
    vms = set(get_backup_vms())
    for vm in list(vms):
        for n in names:
            if n not in vm.name:
                vms.discard(vm)
    return list(vms)


def search_by_uuid(uuid):
    return [vm for vm in get_backup_vms() if vm.uuid == uuid]


args = docopt(__doc__)

if args['list']:
    print_vms(get_backup_vms())
elif args['search']:
    print_vms(search_by_names(args['<search-term>']))
elif args['export']:
    if args['--uuid']:
        found = search_by_uuid(args['--uuid'])
    else:
        found = search_by_names(args['<search-term>'])
    if not found:
        print('No VM found to export')
        exit(2)
    if len(found) > 1:
        print('Multiple VMs found, but you only want to export one.')
        exit(3)
    vm = found[0]
    vm.export(args['--dir'])
elif args['import']:
    check_output(['xe', 'vm-import', 'filename=%s' % args['<filename>']])
elif args['nfs-export-all']:
    nfs_export_all(args['<device>'], args['<folder>'], args['--delete-old'])
