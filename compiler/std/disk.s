# DISK_READ_SECTOR

void disk_read_sector(int sector, int target) {

    // r3, r4 contain parameters
    ADDI r10 r0 -80 // DISK_STATUS
    ADDI r8 r0 4    // MASK for but 2: TX_BUSY
    ADDI r6 255     // MASK 0xFF
    ADDI r7 r0 8    // shift amount = 8

    LW r11 r10 0 // read DISK_STATUS
    AND r13 r11 r8  // Test TBUSY
    BEQ r13 r8 -2
    ADDI r12 r0 r1   // read sector
    SW r12 r10 1 // transmit to ESP

    // wait for channel to open (SEND_SECTOR LOW BYTE)
    LW r11 r10 0 // read DISK_STATUS
    AND r13 r11 r8  // Test TBUSY
    BEQ r13 r8 -2
    AND r12 r6 r3 // sector number
    SW r12 r10 1 // send to ESP


    //((r3 >> 8) & 0xFF) (sector high byte)
    ADDI r19 r0 8
    BEQ r19 r0 4
    SRL  r3, r3, 1
    ADDI r19 r0 -1
    BEQ r0 r0 -3

    // wait for channel to open (SEND_SECTOR HIGH BYTE)
    LW r11 r10 0 // read DISK_STATUS
    AND r13 r7 r8  // Test TBUSY
    BEQ r13 r8 -2
    AND r12 r6 r3 // sector number
    SW r12 r10 1 // send to ESP

    // stream 128 words into memory
    ADDI r14 r0 128 //words to receive
    ADDI r9 r9 1    // Msk for bit 0 RX_READY
    BEQ r14 r0 done

    LW r11 r10 0
    AND r13 r11 r9    // test TX RX_READY
    BEQ r13 r0 -2

    LW r12 r10 1        //pop 32-bit word
    SW r12 r4 0       // store to IRAM
    ADDI r4 r4 1
    ADDI r14 r14 -1
    BEQ r0 r0 -8


}



