 array [0..3] of char;
                  lodadr : integer;
                end;
       fname = string[11];
 var   buf : buffer;
       ring_buf : array [0..255] of byte;
       key_buf : array [0..255] of byte;
       filvar : file;
       file_name : string [11];
       block_number,
       old_interrupt,
       checksum,
       ownlin,
       ownrow,
       othlin,
       othrow,
       old_vec : integer;
       old_rec_vec : integer;
       inter_vec : integer absolute $ffec;
       key_vec : integer absolute $ffe4;
       dma_shadow : integer absolute $ffb3;
       spec_rec : integer absolute $ffee;
       head : ^header;
       flag,
       flag2,
       time_outflag : boolean;
       key,
       to_store,
       to_get,
   