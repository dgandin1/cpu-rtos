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
    VL_IN8(CLK,0,0);
    VL_IN8(RESET,0,0);
    VL_IN8(SA,4,0);
    VL_IN8(SB,4,0);
    VL_IN8(LD,0,0);
    VL_IN8(DR,4,0);
    CData/*0:0*/ regfile__DOT__CLK;
    CData/*0:0*/ regfile__DOT__RESET;
    CData/*4:0*/ regfile__DOT__SA;
    CData/*4:0*/ regfile__DOT__SB;
    CData/*0:0*/ regfile__DOT__LD;
    CData/*4:0*/ regfile__DOT__DR;
    CData/*0:0*/ __VstlFirstIteration;
    CData/*0:0*/ __VstlPhaseResult;
    CData/*0:0*/ __VicoFirstIteration;
    CData/*0:0*/ __VicoPhaseResult;
    CData/*0:0*/ __Vtrigprevexpr___TOP__regfile__DOT__CLK__0;
    CData/*0:0*/ __VactPhaseResult;
    CData/*0:0*/ __VnbaPhaseResult;
    VL_IN(D_in,31,0);
    VL_OUT(DataA,31,0);
    VL_OUT(DataB,31,0);
    IData/*31:0*/ regfile__DOT__D_in;
    IData/*31:0*/ regfile__DOT__DataA;
    IData/*31:0*/ regfile__DOT__DataB;
    IData/*31:0*/ regfile__DOT__i;
    IData/*31:0*/ __VactIterCount;
    VlUnpacked<IData/*31:0*/, 32> regfile__DOT__storage;
    VlUnpacked<QData/*63:0*/, 1> __VstlTriggered;
    VlUnpacked<QData/*63:0*/, 1> __VicoTriggered;
    VlUnpacked<QData/*63:0*/, 1> __VactTriggered;
    VlUnpacked<QData/*63:0*/, 1> __VnbaTriggered;
    VlNBACommitQueue<VlUnpacked<IData/*31:0*/, 32>, false, IData/*31:0*/, 1> __VdlyCommitQueueregfile__DOT__storage;

    // INTERNAL VARIABLES
    Vtop__Syms* vlSymsp;
    const char* vlNamep;

    // CONSTRUCTORS
    Vtop___024root(Vtop__Syms* symsp, const char* namep);
    ~Vtop___024root();
    VL_UNCOPYABLE(Vtop___024root);

    // INTERNAL METHODS
    void __Vconfigure(bool first);
};


#endif  // guard
