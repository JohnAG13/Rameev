/* Generated automatically by Rameev C Transpiler */
#include "rameev_runtime.h"

int main(int argc, char** argv) {
    RValue rv_a = r_none();
    RValue rv_b = r_none();
    RValue rv_c = r_none();
    RValue rv_counter = r_none();
    RValue rv_empty = r_none();
    RValue rv_flag = r_none();
    RValue rv_lst = r_none();
    rv_a = r_int(10LL);
    rv_b = r_dbl(20.5);
    rv_c = r_str("Hello, Rameev on C!");
    rv_flag = r_bool(true);
    rv_empty = r_none();
    r_print(1, rv_c);
    r_print(8, r_str("a ="), rv_a, r_str("b ="), rv_b, r_str("flag ="), rv_flag, r_str("empty ="), rv_empty);
    if (r_truthy(r_and(r_lt(rv_a, r_int(15LL)), rv_flag))) {
        r_print(1, r_str("Условие if сработало успешно!"));
    } else {
        r_print(1, r_str("Ошибка условия"));
    }
    rv_lst = r_list_create(3, r_int(1LL), r_int(2LL), r_int(3LL));
    r_print(2, r_str("Исходный список:"), rv_lst);
    r_print(2, r_str("Длина списка:"), r_len(rv_lst));
    r_print(2, r_str("Элемент с индексом 1:"), r_index(rv_lst, r_int(1LL)));
    r_list_add(rv_lst, r_int(42LL));
    r_print(2, r_str("После add(lst, 42):"), rv_lst);
    r_list_remove(rv_lst, r_int(0LL));
    r_print(2, r_str("После remove(lst, 0):"), rv_lst);
    rv_counter = r_int(0LL);
    while (r_truthy(r_lt(rv_counter, r_int(10LL)))) {
        rv_counter = r_add(rv_counter, r_int(1LL));
        if (r_truthy(r_eq(rv_counter, r_int(3LL)))) {
            continue;
        }
        if (r_truthy(r_gt(rv_counter, r_int(5LL)))) {
            break;
        }
        r_print(2, r_str("counter ="), rv_counter);
    }
    r_print(1, r_str("Тест завершен!"));
    return 0;
}
