// Verilated -*- C++ -*-
// DESCRIPTION: Verilator output: Design internal header
// See Vtop.h for the primary calling header

#ifndef VERILATED_VTOP___024ROOT_H_
#define VERILATED_VTOP___024ROOT_H_  // guard

#include "verilated.h"


class Vtop__Syms;

class alignas(VL_CACHE_LINE_BYTES) Vtop___024root final {
  public:

    // DESIGN SPECIFIC STATE
    // Anonymous structures to workaround compiler member-count bugs
    struct {
        VL_IN8(CLK,0,0);
        VL_IN8(RESET,0,0);
        VL_IN8(IRQ_in,3,0);
        CData/*0:0*/ cpu__DOT__CLK;
        CData/*0:0*/ cpu__DOT__RESET;
        CData/*3:0*/ cpu__DOT__IRQ_in;
        CData/*4:0*/ cpu__DOT__SA;
        CData/*4:0*/ cpu__DOT__SB;
        CData/*0:0*/ cpu__DOT__LD;
        CData/*4:0*/ cpu__DOT__DR;
        CData/*2:0*/ cpu__DOT__FS;
        CData/*0:0*/ cpu__DOT__MB;
        CData/*0:0*/ cpu__DOT__MD;
        CData/*0:0*/ cpu__DOT__MW;
        CData/*0:0*/ cpu__DOT__C;
        CData/*0:0*/ cpu__DOT__V;
        CData/*0:0*/ cpu__DOT__N;
        CData/*0:0*/ cpu__DOT__Z;
        CData/*0:0*/ cpu__DOT__MIE;
        CData/*0:0*/ cpu__DOT__is_mret;
        CData/*3:0*/ cpu__DOT__irq_pending;
        CData/*1:0*/ cpu__DOT__irq_id;
        CData/*1:0*/ cpu__DOT__MCAUSE;
        CData/*0:0*/ cpu__DOT__is_branch;
        CData/*0:0*/ cpu__DOT__branch_taken;
        CData/*2:0*/ cpu__DOT__main__DOT__FS;
        CData/*0:0*/ cpu__DOT__main__DOT__C;
        CData/*0:0*/ cpu__DOT__main__DOT__N;
        CData/*0:0*/ cpu__DOT__main__DOT__Z;
        CData/*0:0*/ cpu__DOT__main__DOT__V;
        CData/*0:0*/ cpu__DOT__main__DOT__BSEL;
        CData/*0:0*/ cpu__DOT__main__DOT__CISEL;
        CData/*1:0*/ cpu__DOT__main__DOT__OSEL;
        CData/*0:0*/ cpu__DOT__main__DOT__SHIFT_LR;
        CData/*0:0*/ cpu__DOT__main__DOT__LOGICAL_OA;
        CData/*1:0*/ cpu__DOT__main__DOT__CSEL;
        CData/*0:0*/ cpu__DOT__main__DOT__C_ADD;
        CData/*0:0*/ cpu__DOT__main__DOT__C_SHIFT;
        CData/*0:0*/ cpu__DOT__main__DOT__V_ADD;
        CData/*0:0*/ cpu__DOT__main__DOT__shift__DOT__LR;
        CData/*0:0*/ cpu__DOT__main__DOT__shift__DOT__C;
        CData/*0:0*/ cpu__DOT__main__DOT__shift__DOT__LSC;
        CData/*0:0*/ cpu__DOT__main__DOT__shift__DOT__RSC;
        CData/*0:0*/ cpu__DOT__main__DOT__ld__DOT__OA;
        CData/*0:0*/ cpu__DOT__main__DOT__add__DOT__CI;
        CData/*0:0*/ cpu__DOT__main__DOT__add__DOT__C;
        CData/*0:0*/ cpu__DOT__main__DOT__add__DOT__V;
        CData/*2:0*/ cpu__DOT__main__DOT__c__DOT__FS;
        CData/*0:0*/ cpu__DOT__main__DOT__c__DOT__BSEL;
        CData/*0:0*/ cpu__DOT__main__DOT__c__DOT__CISEL;
        CData/*1:0*/ cpu__DOT__main__DOT__c__DOT__OSEL;
        CData/*0:0*/ cpu__DOT__main__DOT__c__DOT__SHIFT_LR;
        CData/*0:0*/ cpu__DOT__main__DOT__c__DOT__LOGICAL_OA;
        CData/*1:0*/ cpu__DOT__main__DOT__c__DOT__CSEL;
        CData/*0:0*/ cpu__DOT__data_memory__DOT__CLK;
        CData/*0:0*/ cpu__DOT__data_memory__DOT__MW;
        CData/*0:0*/ cpu__DOT__program_counter__DOT__CLK;
        CData/*0:0*/ cpu__DOT__program_counter__DOT__RESET;
        CData/*0:0*/ cpu__DOT__register__DOT__CLK;
        CData/*0:0*/ cpu__DOT__register__DOT__RESET;
        CData/*4:0*/ cpu__DOT__register__DOT__SA;
        CData/*4:0*/ cpu__DOT__register__DOT__SB;
        CData/*0:0*/ cpu__DOT__register__DOT__LD;
        CData/*4:0*/ cpu__DOT__register__DOT__DR;
    };
    struct {
        CData/*4:0*/ cpu__DOT__decode__DOT__DR;
        CData/*4:0*/ cpu__DOT__decode__DOT__SA;
        CData/*4:0*/ cpu__DOT__decode__DOT__SB;
        CData/*0:0*/ cpu__DOT__decode__DOT__MB;
        CData/*0:0*/ cpu__DOT__decode__DOT__MD;
        CData/*0:0*/ cpu__DOT__decode__DOT__MW;
        CData/*0:0*/ cpu__DOT__decode__DOT__LD;
        CData/*2:0*/ cpu__DOT__decode__DOT__FS;
        CData/*0:0*/ __VstlFirstIteration;
        CData/*0:0*/ __VstlPhaseResult;
        CData/*0:0*/ __VicoFirstIteration;
        CData/*0:0*/ __VicoPhaseResult;
        CData/*0:0*/ __Vtrigprevexpr___TOP__cpu__DOT__CLK__0;
        CData/*0:0*/ __Vtrigprevexpr___TOP__cpu__DOT__RESET__0;
        CData/*0:0*/ __Vtrigprevexpr___TOP__cpu__DOT__data_memory__DOT__CLK__0;
        CData/*0:0*/ __Vtrigprevexpr___TOP__cpu__DOT__program_counter__DOT__CLK__0;
        CData/*0:0*/ __Vtrigprevexpr___TOP__cpu__DOT__program_counter__DOT__RESET__0;
        CData/*0:0*/ __Vtrigprevexpr___TOP__cpu__DOT__register__DOT__CLK__0;
        CData/*0:0*/ __VactPhaseResult;
        CData/*0:0*/ __VnbaPhaseResult;
        SData/*11:0*/ cpu__DOT__IMM;
        SData/*11:0*/ cpu__DOT__decode__DOT__IMM;
        IData/*31:0*/ cpu__DOT__Iin;
        IData/*31:0*/ cpu__DOT__DataA;
        IData/*31:0*/ cpu__DOT__DataB;
        IData/*31:0*/ cpu__DOT__PC_next;
        IData/*31:0*/ cpu__DOT__PC_current;
        IData/*31:0*/ cpu__DOT__D_in;
        IData/*31:0*/ cpu__DOT__SE_IMM;
        IData/*31:0*/ cpu__DOT__finalDataA;
        IData/*31:0*/ cpu__DOT__Alu_Output;
        IData/*31:0*/ cpu__DOT__alu_in_b;
        IData/*31:0*/ cpu__DOT__dram_data_out;
        IData/*31:0*/ cpu__DOT__MEPC;
        IData/*31:0*/ cpu__DOT__pc_standard_next;
        IData/*31:0*/ cpu__DOT__pc_plus_1;
        IData/*31:0*/ cpu__DOT__pc_branch_target;
        IData/*31:0*/ cpu__DOT__main__DOT__A;
        IData/*31:0*/ cpu__DOT__main__DOT__B;
        IData/*31:0*/ cpu__DOT__main__DOT__Y;
        IData/*31:0*/ cpu__DOT__main__DOT__Y_ADD;
        IData/*31:0*/ cpu__DOT__main__DOT__Y_LOGICAL;
        IData/*31:0*/ cpu__DOT__main__DOT__Y_SHIFT;
        IData/*31:0*/ cpu__DOT__main__DOT__shift__DOT__A;
        IData/*31:0*/ cpu__DOT__main__DOT__shift__DOT__Y;
        IData/*31:0*/ cpu__DOT__main__DOT__shift__DOT__LS;
        IData/*31:0*/ cpu__DOT__main__DOT__shift__DOT__RS;
        IData/*31:0*/ cpu__DOT__main__DOT__ld__DOT__A;
        IData/*31:0*/ cpu__DOT__main__DOT__ld__DOT__B;
        IData/*31:0*/ cpu__DOT__main__DOT__ld__DOT__Y;
        IData/*31:0*/ cpu__DOT__main__DOT__add__DOT__A;
        IData/*31:0*/ cpu__DOT__main__DOT__add__DOT__B;
        IData/*31:0*/ cpu__DOT__main__DOT__add__DOT__Y;
        IData/*31:0*/ cpu__DOT__data_memory__DOT__ADDR;
        IData/*31:0*/ cpu__DOT__data_memory__DOT__DATA_IN;
        IData/*31:0*/ cpu__DOT__data_memory__DOT__DATA_OUT;
        IData/*31:0*/ cpu__DOT__instruction_memory__DOT__FETCH_ADDR;
        IData/*31:0*/ cpu__DOT__instruction_memory__DOT__INSTRUCTION;
        IData/*31:0*/ cpu__DOT__program_counter__DOT__NEXT_PC;
        IData/*31:0*/ cpu__DOT__program_counter__DOT__PC;
        IData/*31:0*/ cpu__DOT__register__DOT__D_in;
        IData/*31:0*/ cpu__DOT__register__DOT__DataA;
        IData/*31:0*/ cpu__DOT__register__DOT__DataB;
        IData/*31:0*/ cpu__DOT__register__DOT__i;
    };
    struct {
        IData/*31:0*/ cpu__DOT__decode__DOT__INST;
        IData/*31:0*/ __VactIterCount;
        QData/*32:0*/ cpu__DOT__main__DOT__add__DOT__sum_ext;
        VlUnpacked<IData/*31:0*/, 5056> cpu__DOT__data_memory__DOT__mem;
        VlUnpacked<IData/*31:0*/, 256> cpu__DOT__instruction_memory__DOT__mem;
        VlUnpacked<IData/*31:0*/, 32> cpu__DOT__register__DOT__storage;
        VlUnpacked<QData/*63:0*/, 1> __VstlTriggered;
        VlUnpacked<QData/*63:0*/, 1> __VicoTriggered;
        VlUnpacked<QData/*63:0*/, 1> __VactTriggered;
        VlUnpacked<QData/*63:0*/, 1> __VnbaTriggered;
    };
    VlNBACommitQueue<VlUnpacked<IData/*31:0*/, 32>, false, IData/*31:0*/, 1> __VdlyCommitQueuecpu__DOT__register__DOT__storage;

    // INTERNAL VARIABLES
    Vtop__Syms* vlSymsp;
    const char* vlNamep;

    // PARAMETERS
    static constexpr CData/*2:0*/ cpu__DOT__main__DOT__c__DOT__FS_ADD = 0U;
    static constexpr CData/*2:0*/ cpu__DOT__main__DOT__c__DOT__FS_SUB = 1U;
    static constexpr CData/*2:0*/ cpu__DOT__main__DOT__c__DOT__FS_SRL = 2U;
    static constexpr CData/*2:0*/ cpu__DOT__main__DOT__c__DOT__FS_SLL = 3U;
    static constexpr CData/*2:0*/ cpu__DOT__main__DOT__c__DOT__FS_AND = 4U;
    static constexpr CData/*2:0*/ cpu__DOT__main__DOT__c__DOT__FS_OR = 6U;
    static constexpr CData/*6:0*/ cpu__DOT__decode__DOT__OP_ARITH = 0x33U;
    static constexpr CData/*6:0*/ cpu__DOT__decode__DOT__OP_IMM_ARITH = 0x13U;
    static constexpr CData/*6:0*/ cpu__DOT__decode__DOT__OP_BRANCH = 0x63U;
    static constexpr CData/*6:0*/ cpu__DOT__decode__DOT__OP_LW = 3U;
    static constexpr CData/*6:0*/ cpu__DOT__decode__DOT__OP_SW = 0x23U;
    static constexpr CData/*6:0*/ cpu__DOT__decode__DOT__OP_JMP = 0x27U;
    static constexpr CData/*2:0*/ cpu__DOT__decode__DOT__FS_ADD = 0U;
    static constexpr CData/*2:0*/ cpu__DOT__decode__DOT__FS_SUB = 1U;
    static constexpr CData/*2:0*/ cpu__DOT__decode__DOT__FS_SRL = 2U;
    static constexpr CData/*2:0*/ cpu__DOT__decode__DOT__FS_SLL = 3U;
    static constexpr CData/*2:0*/ cpu__DOT__decode__DOT__FS_AND = 4U;
    static constexpr CData/*2:0*/ cpu__DOT__decode__DOT__FS_OR = 6U;
    static constexpr CData/*2:0*/ cpu__DOT__decode__DOT__FS_XOR = 7U;
    static constexpr SData/*11:0*/ cpu__DOT__decode__DOT__IMM_DC = 0U;
    static constexpr IData/*31:0*/ cpu__DOT__MTVEC = 4U;

    // CONSTRUCTORS
    Vtop___024root(Vtop__Syms* symsp, const char* namep);
    ~Vtop___024root();
    VL_UNCOPYABLE(Vtop___024root);

    // INTERNAL METHODS
    void __Vconfigure(bool first);
};


#endif  // guard
