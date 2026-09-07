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
