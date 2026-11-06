/* Generated automatically by Rameev C Transpiler */
#include "rameev_runtime.h"

int main(int argc, char** argv) {
    RValue rv_a = r_none();
    RValue rv_i = r_none();
    rv_i = r_to_int(r_int(8LL));
    rv_a = r_int(0LL);
    while (r_truthy(r_gt(rv_i, r_int(0LL)))) {
        r_print(2, r_mul(r_str(" "), rv_a), r_mul(r_str("*"), rv_i));
        rv_i = r_sub(rv_i, r_int(1LL));
        rv_a = r_add(rv_a, r_int(1LL));
    }
    return 0;
}
