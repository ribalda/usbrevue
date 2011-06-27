#!/usr/bin/env python
from struct import unpack_from, pack_into
import array
import datetime

class Packet(object):
    def __init__(self, hdr, pack):
        if len(pack) < 64:
            raise RuntimeError("Not a USB Packet")

        self.id,          = unpack_from('=Q', pack)
        self.type,        = unpack_from('=c', pack, 8)
        self.xfer_type,   = unpack_from('=B', pack, 9)

        if self.type not in ['C', 'S', 'E'] or self.xfer_type not in range(4):
            raise RuntimeError("Not a USB Packet")

        self.epnum,       = unpack_from('=B', pack, 10)
        self.devnum,      = unpack_from('=B', pack, 11)
        self.busnum,      = unpack_from('=H', pack, 12)
        self.flag_setup,  = unpack_from('=c', pack, 14)
        self.flag_data,   = unpack_from('=c', pack, 15)
        self.ts_sec,      = unpack_from('=q', pack, 16)
        self.ts_usec,     = unpack_from('=i', pack, 24)
        self.status,      = unpack_from('=i', pack, 28)
        self.length,      = unpack_from('=I', pack, 32)
        self.len_cap,     = unpack_from('=I', pack, 36)
        # setup is only meaningful if flag_setup == 's'
        self.setup = list(unpack_from('=8B', pack, 40))
        # error_count and numdesc are only meaningful for isochronous transfers
        # (xfer_type == 0)
        self.error_count, = unpack_from('=i', pack, 40)
        self.numdesc,     = unpack_from('=i', pack, 44)
        # interval is only meaningful for isochronous or interrupt transfers
        # (xfer_type in [0,1])
        self.interval,    = unpack_from('=i', pack, 48)
        # start_frame is only meaningful for isochronous transfers
        self.start_frame, = unpack_from('=i', pack, 52)
        self.xfer_flags,  = unpack_from('=I', pack, 56)
        self.ndesc,       = unpack_from('=I', pack, 60)

        datalen = len(pack) - 64
        self.data = list(unpack_from('=%dB' % datalen, pack, 64))
        self.hdr, self.pack = hdr, pack

    def copy(self):
        new_packet = Packet(self.hdr, self.pack)
        return new_packet


    def print_pcap_fields(self):
        """ 
        Print detailed packet information for debug purposes.    
        Assumes header exists.
        """
        print "id = %d" % (self.id)
        print "type = %s" % (self.type)
        print "xfer_type = %d" % (self.xfer_type)
        print "epnum = %d" % (self.epnum)
        print "devnum = %d" % (self.devnum)
        print "busnum = %d" % (self.busnum)
        print "flag_setup = %s" % (self.flag_setup)
        print "flag_data = %s" % (self.flag_data)
        print "ts_sec = %d" % (self.ts_sec,)
        print "ts_usec = %d" % (self.ts_usec)
        print "status = %d" % (self.status)
        print "length = %d" % (self.length)
        print "len_cap = %d" % (self.len_cap)
        # setup is only meaningful if flag_setup == 's')
        if (self.flag_setup == 's'):
            print "setup = %d" % (self.setup)
        # error_count and numdesc are only meaningful for isochronous transfers
        # (xfer_type == 0)
        if (self.xfer_type == 0):
            print "error_count = %d" % (self.error_count)
            print "numdesc = %d" % (self.numdesc)
        # interval is only meaningful for isochronous or interrupt transfers)
        # (xfer_type in [0,1]))
        if (self.xfer_type in [0,1]):
            print "interval = %d" % (self.interval)
        # start_frame is only meaningful for isochronous transfers)
        if (self.xfer_type == 0):
            print "start_frame = %d" % (self.start_frame)
        print "xfer_flags = %d" % (self.xfer_flags)
        print "ndesc = %d" % (self.ndesc)
        # print "datalen = " % (datalen)
        # print "data = " % (self.data)
        print "data =", self.data
        # print "hdr = " % (self.hdr)
        print "hdr =", self.hdr
        # print "packet = " % (self.pack)


    def print_pcap_summary(self):
        """ 
        Print concise packet summary information for debug purposes.    
        Assumes header exists.
        """
        print ('%s: Captured %d bytes, truncated to %d bytes' % (
                datetime.datetime.now(), self.hdr.getlen(),
                self.hdr.getcaplen()))


    def repack(self):
        """
        Returns a binary string of the packet information. Currently
        ignores changes to anything but data.
        """
        modified_pack = array.array('c', '\0' * 64)

        pack_into('=Q', modified_pack, 0, self.id)
        pack_into('=c', modified_pack, 8, self.type)
        pack_into('=B', modified_pack, 9, self.xfer_type)
        pack_into('=B', modified_pack, 10, self.epnum)
        pack_into('=B', modified_pack, 11, self.devnum)
        pack_into('=H', modified_pack, 12, self.busnum)
        pack_into('=c', modified_pack, 14, self.flag_setup)
        pack_into('=c', modified_pack, 15, self.flag_data)
        pack_into('=q', modified_pack, 16, self.ts_sec)
        pack_into('=i', modified_pack, 24, self.ts_usec)
        pack_into('=i', modified_pack, 28, self.status)
        pack_into('=I', modified_pack, 32, self.length)
        pack_into('=I', modified_pack, 36, self.len_cap)
        if self.flag_setup == 's':
            i = 40
            for c in setup:
                modified_pack[i] = chr(c)
                i += 1
        else:
            pack_into('=i', modified_pack, 40, self.error_count)
            pack_into('=i', modified_pack, 44, self.numdesc)
        pack_into('=i', modified_pack, 48, self.interval)
        pack_into('=i', modified_pack, 52, self.start_frame)
        pack_into('=I', modified_pack, 56, self.xfer_flags)
        pack_into('=I', modified_pack, 60, self.ndesc)

        # return self.pack[:64] + ''.join(map(chr, self.data))
        return modified_pack.tostring() + ''.join(map(chr, self.data))
        

if __name__ == '__main__':
    # read a pcap file from stdin, replace the first byte of any data found
    # with 0x42, and write the modified packets to stdout
    import pcapy
    pcap = pcapy.open_offline('-')
    out = pcap.dump_open('-')

    while 1:
        hdr, pack = pcap.next()
        if hdr is None:
            break # EOF
        p = Packet(hdr, pack)
        p.print_pcap_fields()
        p.print_pcap_summary()
        if len(p.data) > 0:
            p.data[0] = 0x42
        out.dump(hdr, p.repack())

