int ball_x = 10;
int ball_y = 10;
int paddle_y = 24;
int ball_vel_x = 1;
int ball_vel_y = 1;
int last_input = 0;

void display_rect(int x, int y, int w, int h) {

    int i = 0;
    int j = 0;
    while (i < w) {
        j = 0;
        while (j < h) {
            on_pixel(x+i, y+j);
            j = j + 1;
        }
        i = i + 1;
    }

}

int main() {

    pit_ldvalue(__long__(50000));
    
}

void IRQ_handler() {
    
    int cause = get_mcause();
    if (cause == 3) {
        clear_screen();
        ball_x = ball_x + ball_vel_x;
        ball_y = ball_y + ball_vel_y;
        if (ball_x == 46) {
            if (ball_y > paddle_y) {
                if (ball_y < paddle_y + 10) {
                    ball_vel_x = mul(ball_vel_x, -1);
                }
            }
        }
        if (ball_x < 1) {
            ball_vel_x = mul(ball_vel_x, -1);
        }
        if (ball_y < 1) {
            ball_vel_y = mul(ball_vel_y, -1);
        }
        if (ball_y > 61) {
            ball_vel_y = mul(ball_vel_y, -1);
        }
        if (ball_x > 62) {
            while (1 == 1) {

            }
        }
        display_rect(ball_x, ball_y, 2, 2);
        display_rect(48, paddle_y, 2, 10);
            
    }
    if (cause == 1) {
        paddle_y = paddle_y - 2;
    }
    if (cause == 2) {
        paddle_y = paddle_y + 2;
    }
    
}
