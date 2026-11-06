#define FPGA_RX_PIN 16
#define FPGA_TX_PIN 17
#define FPGA_BAUD   115200

#define SECTOR_WORDS 128  // 128 words = 512 bytes per sector
#define TOTAL_SECTORS 4   // Example: 4 sectors in virtual disk (2 KB)


HardwareSerial FpgaSerial(2);

const uint32_t disk_image[TOTAL_SECTORS][SECTOR_WORDS] = {
    // --- Sector 0: Initial Boot Code ---
    {
        0x00a00113,  // ADDI r2, r0, 10
        0x01400193,  // ADDI r3, r0, 20
        0x00310233,  // ADD  r4, r2, r3  (r4 = 30)
        0x00000063   // BEQ  r0, r0, 0   (Halt loop)
            // (Remaining 124 words will pad with 0x00000013 / NOPs)
    },
        // --- Sector 1: Next Program / Stage ---
    {
        0x06400113,  // ADDI r2, r0, 100
        0x0c800193,  // ADDI r3, r0, 200
        0x00310233,  // ADD  r4, r2, r3  (r4 = 300)
        0x00000063   // BEQ  r0, r0, 0
    }
};


const size_t PROGRAM_SIZE = sizeof(program_payload) / sizeof(program_payload[0]);

void send_word32(uint32_t word) {
    FpgaSerial.write((uint8_t)(word & 0xFF));
    FpgaSerial.write((uint8_t)((word >> 8) & 0xFF));
    FpgaSerial.write((uint8_t)((word >> 16) & 0xFF));
    FpgaSerial.write((uint8_t)((word >> 24) & 0xFF));
}



void setup() {
    Serial.begin(115200);
    FpgaSerial.begin(FPGA_BAUD, SERIAL_8N1, FPGA_RX_PIN, FPGA_TX_PIN);

    Serial.println("\n[ESP32] Virtual Disk Controller Ready.");
    Serial.println("[ESP32] Listening for CPU sector requests...");
}

 void loop() {
    // Wait until CPU sends at least 3 bytes: [CMD] [SECTOR_L] [SECTOR_H]
    if (FpgaSerial.available() >= 3) {
        uint8_t cmd       = FpgaSerial.read();
        uint8_t sec_l     = FpgaSerial.read();
        uint8_t sec_h     = FpgaSerial.read();
        uint16_t sector_num = (sec_h << 8) | sec_l;

        if (cmd == 0x01) { // CMD_READ_SECTOR
            Serial.printf("[ESP32] Read request for Sector %u received.\n", sector_num);

            if (sector_num < TOTAL_SECTORS) {
                // Stream 128 words to the FPGA
                for (int i = 0; i < SECTOR_WORDS; i++) {
                    uint32_t word = disk_image[sector_num][i];
                    // Default uninitialized words to NOP (0x00000013)
                    if (word == 0) word = 0x00000013;
                    send_word32(word);
                    delayMicroseconds(50); // Small pacing delay to avoid buffer overflow
                }
                Serial.printf("[ESP32] Streamed Sector %u (128 words) to FPGA.\n", sector_num);
            } else {
                Serial.printf("[ESP32] ERROR: Sector %u out of bounds!\n", sector_num);
                // Return 128 zero words on error
                for (int i = 0; i < SECTOR_WORDS; i++) send_word32(0);
            }
        }
    }
}


