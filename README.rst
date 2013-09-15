Simple Xen Backup Solution
==========================

I present you here a simple backup solution for XenServer 6.2 (other versions
not tested). You need an nfs enabled device (e.g. NAS) to backup your VMs
there.

This solution includes a backported `docopt
<https://github.com/docopt/docopt>`_, because XenServer 6.2 is still using
Python 2.4. Why didn't I use ``optparse``? Because docopt is A-W-E-S-O-M-E.
Seriously. Never write a terminal application without it.

I've done this with a WD NAS, that's why you'll see ``/DataVolume/shares/``,
but you can change that to your own address.

License: MIT - see ``LICENSE.txt``.

Source available `here <https://github.com/davidhalter-archive/xen_backup>`_.


Configuring a daily backup
==========================

To use a backup you can use something like this (same syntax as ``mount``)::

    ./backup.py nfs-export-all backup.company.local:/DataVolume/shares/xenserver/ /media/backup --delete-old

Then add this a `/etc/crontab` line, e.g. like this::

    01 2 * * * root /root/xen_backup/backup.py nfs-export-all backup.company.local:/DataVolume/shares/xenserver/ /media/backup --delete-old


Configuring NFS on the NAS
==========================

You have to configure NFS on the NAS, to make it possible for Python script to
work::

    /DataVolume/shares/xenserver xenserver.company.local(rw,sync,no_subtree_check)
