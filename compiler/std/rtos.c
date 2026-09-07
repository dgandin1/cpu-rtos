int *head_ptr = 1500;

struct pcb {
    int *stack_pointer;
    int stack_size;
    struct pcb *next;
};

struct pcb *head;

int* malloc(int size) {

    int* allocated_mem = head_ptr;

    head_ptr = head_ptr + size;

    return allocated_mem;

}

void register_task(int *function_address) {

    struct pcb *new_task = malloc(3);
    int stack_size = 50;
    int *task_stack = malloc(stack_size);

    int *initial_sp = task_stack + stack_size;
    initial_sp = initial_sp - 33;
    
    int *mepc_ptr = initial_sp + 31;
    *mepc_ptr = function_address;

    (*new_task).stack_pointer = initial_sp;
    (*new_task).stack_size = stack_size;
    
    (*new_task).next = head;
    head = new_task;

}

void init_rr() {

    struct pcb *current = head;

    while ((*current).next != 0) {
        current = (*current).next;
    }

    (*current).next = head;

    pit_ldvalue(__long__(200000));

    __save_sp((*head).stack_pointer);

    __asm__("LW r27 r1 31");
    __asm__("LW r31 r1 30");
    __asm__("LW r30 r1 29");
    __asm__("LW r29 r1 28");
    __asm__("LW r28 r1 27");
    __asm__("LW r26 r1 26");
    __asm__("LW r25 r1 25");
    __asm__("LW r24 r1 24");
    __asm__("LW r23 r1 23");
    __asm__("LW r22 r1 22");
    __asm__("LW r21 r1 21");
    __asm__("LW r20 r1 20");
    __asm__("LW r19 r1 19");
    __asm__("LW r18 r1 18");
    __asm__("LW r17 r1 17");
    __asm__("LW r16 r1 16");
    __asm__("LW r15 r1 15");
    __asm__("LW r14 r1 14");
    __asm__("LW r13 r1 13");
    __asm__("LW r12 r1 12");
    __asm__("LW r11 r1 11");
    __asm__("LW r10 r1 10");
    __asm__("LW r9 r1 9");
    __asm__("LW r8 r1 8");
    __asm__("LW r7 r1 7");
    __asm__("LW r6 r1 6");
    __asm__("LW r5 r1 5");
    __asm__("LW r4 r1 4");
    __asm__("LW r3 r1 3");
    __asm__("LW r2 r1 2");
    
    __asm__("ADDI r1 r1 33");

    __asm__("MRET");

}

void IRQ_handler() {

    __asm__("ADDI r1 r1 -32");
    __asm__("SW r2 r1 2");
    __asm__("SW r3 r1 3");
    __asm__("SW r4 r1 4");
    __asm__("SW r5 r1 5");
    __asm__("SW r6 r1 6");
    __asm__("SW r7 r1 7");
    __asm__("SW r8 r1 8");
    __asm__("SW r9 r1 9");
    __asm__("SW r10 r1 10");
    __asm__("SW r11 r1 11");
    __asm__("SW r12 r1 12");
    __asm__("SW r13 r1 13");
    __asm__("SW r14 r1 14");
    __asm__("SW r15 r1 15");
    __asm__("SW r16 r1 16");
    __asm__("SW r17 r1 17");
    __asm__("SW r18 r1 18");
    __asm__("SW r19 r1 19");
    __asm__("SW r20 r1 20");
    __asm__("SW r21 r1 21");
    __asm__("SW r22 r1 22");
    __asm__("SW r23 r1 23");
    __asm__("SW r24 r1 24");
    __asm__("SW r25 r1 25");
    __asm__("SW r26 r1 26");
    __asm__("SW r28 r1 27");
    __asm__("SW r29 r1 28");
    __asm__("SW r30 r1 29");
    __asm__("SW r31 r1 30");
    __asm__("SW r27 r1 31");

    (*head).stack_pointer = __get_sp();
    head = (*head).next;
    __save_sp((*head).stack_pointer);

    __asm__("LW r27 r1 31");

    __asm__("LW r27 r1 31");
    __asm__("LW r31 r1 30");
    __asm__("LW r30 r1 29");
    __asm__("LW r29 r1 28");
    __asm__("LW r28 r1 27");
    __asm__("LW r26 r1 26");
    __asm__("LW r25 r1 25");
    __asm__("LW r24 r1 24");
    __asm__("LW r23 r1 23");
    __asm__("LW r22 r1 22");
    __asm__("LW r21 r1 21");
    __asm__("LW r20 r1 20");
    __asm__("LW r19 r1 19");
    __asm__("LW r18 r1 18");
    __asm__("LW r17 r1 17");
    __asm__("LW r16 r1 16");
    __asm__("LW r15 r1 15");
    __asm__("LW r14 r1 14");
    __asm__("LW r13 r1 13");
    __asm__("LW r12 r1 12");
    __asm__("LW r11 r1 11");
    __asm__("LW r10 r1 10");
    __asm__("LW r9 r1 9");
    __asm__("LW r8 r1 8");
    __asm__("LW r7 r1 7");
    __asm__("LW r6 r1 6");
    __asm__("LW r5 r1 5");
    __asm__("LW r4 r1 4");
    __asm__("LW r3 r1 3");
    __asm__("LW r2 r1 2");
    
    __asm__("ADDI r1 r1 32");

}