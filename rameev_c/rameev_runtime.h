/**
 * rameev_runtime.h
 * Runtime library for Rameev programming language compiled to C.
 */

#ifndef RAMEEV_RUNTIME_H
#define RAMEEV_RUNTIME_H

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdbool.h>
#include <stdarg.h>
#include <math.h>

typedef enum {
    R_NONE,
    R_INT,
    R_DOUBLE,
    R_BOOL,
    R_STRING,
    R_LIST
} RType;

typedef struct RValue RValue;

typedef struct RList {
    RValue* items;
    int count;
    int capacity;
} RList;

struct RValue {
    RType type;
    union {
        long long int_val;
        double dbl_val;
        bool bool_val;
        char* str_val;
        RList* list_val;
    };
};

static void r_error(const char* msg) {
    fprintf(stderr, "Ошибка выполнения (C Runtime): %s\n", msg);
    exit(1);
}

static inline RValue r_none(void) {
    RValue v;
    v.type = R_NONE;
    v.int_val = 0;
    return v;
}

static inline RValue r_int(long long n) {
    RValue v;
    v.type = R_INT;
    v.int_val = n;
    return v;
}

static inline RValue r_dbl(double d) {
    RValue v;
    v.type = R_DOUBLE;
    v.dbl_val = d;
    return v;
}

static inline RValue r_bool(bool b) {
    RValue v;
    v.type = R_BOOL;
    v.bool_val = b;
    return v;
}

static inline RValue r_str(const char* s) {
    RValue v;
    v.type = R_STRING;
    if (s == NULL) {
        v.str_val = (char*)malloc(1);
        v.str_val[0] = '\0';
    } else {
        size_t len = strlen(s);
        v.str_val = (char*)malloc(len + 1);
        strcpy(v.str_val, s);
    }
    return v;
}

static inline RValue r_list_create(int count, ...) {
    RValue v;
    v.type = R_LIST;
    RList* list = (RList*)malloc(sizeof(RList));
    list->count = count;
    list->capacity = count < 4 ? 4 : count * 2;
    list->items = (RValue*)malloc(sizeof(RValue) * list->capacity);

    va_list args;
    va_start(args, count);
    for (int i = 0; i < count; i++) {
        list->items[i] = va_arg(args, RValue);
    }
    va_end(args);

    v.list_val = list;
    return v;
}

static char* r_format(RValue v);

static char* r_format(RValue v) {
    char buf[128];
    switch (v.type) {
        case R_NONE:
            return strdup("none");
        case R_BOOL:
            return strdup(v.bool_val ? "True" : "False");
        case R_INT:
            snprintf(buf, sizeof(buf), "%lld", v.int_val);
            return strdup(buf);
        case R_DOUBLE: {
            snprintf(buf, sizeof(buf), "%g", v.dbl_val);
            return strdup(buf);
        }
        case R_STRING:
            return strdup(v.str_val);
        case R_LIST: {
            size_t total_len = 3; // "[ ]\0"
            char** parts = (char**)malloc(sizeof(char*) * (v.list_val->count > 0 ? v.list_val->count : 1));
            for (int i = 0; i < v.list_val->count; i++) {
                parts[i] = r_format(v.list_val->items[i]);
                total_len += strlen(parts[i]) + 2;
            }
            char* out = (char*)malloc(total_len);
            strcpy(out, "[");
            for (int i = 0; i < v.list_val->count; i++) {
                if (i > 0) strcat(out, ", ");
                strcat(out, parts[i]);
                free(parts[i]);
            }
            strcat(out, "]");
            free(parts);
            return out;
        }
    }
    return strdup("");
}

static inline void r_print(int count, ...) {
    va_list args;
    va_start(args, count);
    for (int i = 0; i < count; i++) {
        RValue val = va_arg(args, RValue);
        char* str = r_format(val);
        printf("%s", str);
        free(str);
        if (i < count - 1) {
            printf(" ");
        }
    }
    va_end(args);
    printf("\n");
    fflush(stdout);
}

static inline bool r_truthy(RValue v) {
    switch (v.type) {
        case R_NONE:
            return false;
        case R_BOOL:
            return v.bool_val;
        case R_INT:
            return v.int_val != 0;
        case R_DOUBLE:
            return v.dbl_val != 0.0;
        case R_STRING:
            return v.str_val != NULL && strlen(v.str_val) > 0;
        case R_LIST:
            return v.list_val != NULL && v.list_val->count > 0;
    }
    return true;
}

static inline RValue r_len(RValue v) {
    if (v.type == R_STRING) {
        return r_int((long long)strlen(v.str_val));
    }
    if (v.type == R_LIST) {
        return r_int((long long)v.list_val->count);
    }
    r_error("len() работает только со строками и списками");
    return r_none();
}

static inline RValue r_to_int(RValue v) {
    if (v.type == R_INT) return v;
    if (v.type == R_BOOL) return r_int(v.bool_val ? 1 : 0);
    if (v.type == R_DOUBLE) return r_int((long long)v.dbl_val);
    if (v.type == R_STRING) {
        char* endptr;
        long long val = strtoll(v.str_val, &endptr, 10);
        if (*endptr != '\0') {
            r_error("Не могу преобразовать строку в целое число");
        }
        return r_int(val);
    }
    r_error("int() не может преобразовать указанное значение");
    return r_none();
}

static inline RValue r_to_dbl(RValue v) {
    if (v.type == R_DOUBLE) return v;
    if (v.type == R_INT) return r_dbl((double)v.int_val);
    if (v.type == R_BOOL) return r_dbl(v.bool_val ? 1.0 : 0.0);
    if (v.type == R_STRING) {
        char* endptr;
        double val = strtod(v.str_val, &endptr);
        if (*endptr != '\0') {
            r_error("Не могу преобразовать строку в число");
        }
        return r_dbl(val);
    }
    r_error("dbl() не может преобразовать указанное значение");
    return r_none();
}

static inline RValue r_to_str(RValue v) {
    char* s = r_format(v);
    RValue res = r_str(s);
    free(s);
    return res;
}

static inline RValue r_gud(int count, ...) {
    if (count == 1) {
        va_list args;
        va_start(args, count);
        RValue prompt = va_arg(args, RValue);
        char* pstr = r_format(prompt);
        printf("%s", pstr);
        fflush(stdout);
        free(pstr);
        va_end(args);
    }
    char buf[1024];
    if (fgets(buf, sizeof(buf), stdin) != NULL) {
        size_t len = strlen(buf);
        if (len > 0 && (buf[len - 1] == '\n' || buf[len - 1] == '\r')) {
            buf[len - 1] = '\0';
        }
        if (len > 1 && buf[len - 2] == '\r') {
            buf[len - 2] = '\0';
        }
        return r_str(buf);
    }
    return r_str("");
}

static inline RValue r_list_add(RValue list_val, RValue item) {
    if (list_val.type != R_LIST) {
        r_error("Первый аргумент add() должен быть списком");
    }
    RList* list = list_val.list_val;
    if (list->count > 0) {
        bool all_num = true;
        bool all_str = true;
        for (int i = 0; i < list->count; i++) {
            if (list->items[i].type != R_INT && list->items[i].type != R_DOUBLE) all_num = false;
            if (list->items[i].type != R_STRING) all_str = false;
        }
        if (all_num && (item.type != R_INT && item.type != R_DOUBLE)) {
            r_error("В числовой список можно добавлять только числа");
        }
        if (all_str && item.type != R_STRING) {
            item = r_to_str(item);
        }
    }
    if (list->count >= list->capacity) {
        list->capacity = list->capacity < 4 ? 4 : list->capacity * 2;
        list->items = (RValue*)realloc(list->items, sizeof(RValue) * list->capacity);
    }
    list->items[list->count++] = item;
    return r_none();
}

static inline RValue r_list_remove(RValue list_val, RValue idx_val) {
    if (list_val.type != R_LIST) {
        r_error("Первый аргумент remove() должен быть списком");
    }
    if (idx_val.type != R_INT) {
        r_error("Индекс для remove() должен быть целым числом");
    }
    RList* list = list_val.list_val;
    long long idx = idx_val.int_val;
    if (idx < 0 || idx >= list->count) {
        r_error("Индекс для remove() вне диапазона");
    }
    for (int i = (int)idx; i < list->count - 1; i++) {
        list->items[i] = list->items[i + 1];
    }
    list->count--;
    return r_none();
}

static inline RValue r_index(RValue coll, RValue idx_val) {
    if (idx_val.type != R_INT) {
        r_error("Индекс должен быть целым числом");
    }
    long long idx = idx_val.int_val;
    if (coll.type == R_STRING) {
        size_t len = strlen(coll.str_val);
        if (idx < 0 || idx >= (long long)len) {
            r_error("Индекс строки вне диапазона");
        }
        char temp[2] = { coll.str_val[idx], '\0' };
        return r_str(temp);
    }
    if (coll.type == R_LIST) {
        RList* list = coll.list_val;
        if (idx < 0 || idx >= list->count) {
            r_error("Индекс списка вне диапазона");
        }
        return list->items[idx];
    }
    r_error("Индексация поддерживается только для списков и строк");
    return r_none();
}

/* --- ОПЕРАТОРЫ --- */

static inline RValue r_add(RValue a, RValue b) {
    if (a.type == R_STRING || b.type == R_STRING) {
        char* sa = r_format(a);
        char* sb = r_format(b);
        size_t len = strlen(sa) + strlen(sb);
        char* out = (char*)malloc(len + 1);
        strcpy(out, sa);
        strcat(out, sb);
        free(sa);
        free(sb);
        RValue res = r_str(out);
        free(out);
        return res;
    }
    if (a.type == R_INT && b.type == R_INT) {
        return r_int(a.int_val + b.int_val);
    }
    if ((a.type == R_INT || a.type == R_DOUBLE) && (b.type == R_INT || b.type == R_DOUBLE)) {
        double da = a.type == R_INT ? (double)a.int_val : a.dbl_val;
        double db = b.type == R_INT ? (double)b.int_val : b.dbl_val;
        return r_dbl(da + db);
    }
    r_error("Операция '+' не поддерживается для этих типов");
    return r_none();
}

static inline RValue r_sub(RValue a, RValue b) {
    if (a.type == R_INT && b.type == R_INT) {
        return r_int(a.int_val - b.int_val);
    }
    if ((a.type == R_INT || a.type == R_DOUBLE) && (b.type == R_INT || b.type == R_DOUBLE)) {
        double da = a.type == R_INT ? (double)a.int_val : a.dbl_val;
        double db = b.type == R_INT ? (double)b.int_val : b.dbl_val;
        return r_dbl(da - db);
    }
    r_error("Операция '-' требует чисел");
    return r_none();
}

static inline RValue r_mul(RValue a, RValue b) {
    // Строка * число
    if (a.type == R_STRING && b.type == R_INT) {
        long long count = b.int_val;
        if (count <= 0) return r_str("");
        size_t len = strlen(a.str_val);
        char* out = (char*)malloc(len * count + 1);
        out[0] = '\0';
        for (long long i = 0; i < count; i++) {
            strcat(out, a.str_val);
        }
        RValue res = r_str(out);
        free(out);
        return res;
    }
    if (a.type == R_INT && b.type == R_STRING) {
        return r_mul(b, a);
    }
    if (a.type == R_INT && b.type == R_INT) {
        return r_int(a.int_val * b.int_val);
    }
    if ((a.type == R_INT || a.type == R_DOUBLE) && (b.type == R_INT || b.type == R_DOUBLE)) {
        double da = a.type == R_INT ? (double)a.int_val : a.dbl_val;
        double db = b.type == R_INT ? (double)b.int_val : b.dbl_val;
        return r_dbl(da * db);
    }
    r_error("Операция '*' не поддерживается для этих типов");
    return r_none();
}

static inline RValue r_div(RValue a, RValue b) {
    if ((a.type == R_INT || a.type == R_DOUBLE) && (b.type == R_INT || b.type == R_DOUBLE)) {
        double db = b.type == R_INT ? (double)b.int_val : b.dbl_val;
        if (db == 0.0) {
            r_error("Деление на ноль");
        }
        double da = a.type == R_INT ? (double)a.int_val : a.dbl_val;
        return r_dbl(da / db);
    }
    r_error("Операция '/' требует чисел");
    return r_none();
}

static inline RValue r_eq(RValue a, RValue b) {
    if (a.type != b.type) {
        if ((a.type == R_INT || a.type == R_DOUBLE) && (b.type == R_INT || b.type == R_DOUBLE)) {
            double da = a.type == R_INT ? (double)a.int_val : a.dbl_val;
            double db = b.type == R_INT ? (double)b.int_val : b.dbl_val;
            return r_bool(da == db);
        }
        return r_bool(false);
    }
    switch (a.type) {
        case R_NONE: return r_bool(true);
        case R_BOOL: return r_bool(a.bool_val == b.bool_val);
        case R_INT: return r_bool(a.int_val == b.int_val);
        case R_DOUBLE: return r_bool(a.dbl_val == b.dbl_val);
        case R_STRING: return r_bool(strcmp(a.str_val, b.str_val) == 0);
        case R_LIST: return r_bool(a.list_val == b.list_val);
    }
    return r_bool(false);
}

static inline RValue r_neq(RValue a, RValue b) {
    RValue eq = r_eq(a, b);
    return r_bool(!eq.bool_val);
}

static inline RValue r_lt(RValue a, RValue b) {
    if ((a.type == R_INT || a.type == R_DOUBLE) && (b.type == R_INT || b.type == R_DOUBLE)) {
        double da = a.type == R_INT ? (double)a.int_val : a.dbl_val;
        double db = b.type == R_INT ? (double)b.int_val : b.dbl_val;
        return r_bool(da < db);
    }
    r_error("Операция '<' требует чисел");
    return r_none();
}

static inline RValue r_gt(RValue a, RValue b) {
    if ((a.type == R_INT || a.type == R_DOUBLE) && (b.type == R_INT || b.type == R_DOUBLE)) {
        double da = a.type == R_INT ? (double)a.int_val : a.dbl_val;
        double db = b.type == R_INT ? (double)b.int_val : b.dbl_val;
        return r_bool(da > db);
    }
    r_error("Операция '>' требует чисел");
    return r_none();
}

static inline RValue r_lte(RValue a, RValue b) {
    if ((a.type == R_INT || a.type == R_DOUBLE) && (b.type == R_INT || b.type == R_DOUBLE)) {
        double da = a.type == R_INT ? (double)a.int_val : a.dbl_val;
        double db = b.type == R_INT ? (double)b.int_val : b.dbl_val;
        return r_bool(da <= db);
    }
    r_error("Операция '<=' требует чисел");
    return r_none();
}

static inline RValue r_gte(RValue a, RValue b) {
    if ((a.type == R_INT || a.type == R_DOUBLE) && (b.type == R_INT || b.type == R_DOUBLE)) {
        double da = a.type == R_INT ? (double)a.int_val : a.dbl_val;
        double db = b.type == R_INT ? (double)b.int_val : b.dbl_val;
        return r_bool(da >= db);
    }
    r_error("Операция '>=' требует чисел");
    return r_none();
}

static inline RValue r_and(RValue a, RValue b) {
    if (!r_truthy(a)) return a;
    return b;
}

static inline RValue r_or(RValue a, RValue b) {
    if (r_truthy(a)) return a;
    return b;
}

static inline RValue r_not(RValue a) {
    return r_bool(!r_truthy(a));
}

static inline RValue r_neg(RValue a) {
    if (a.type == R_INT) return r_int(-a.int_val);
    if (a.type == R_DOUBLE) return r_dbl(-a.dbl_val);
    r_error("Унарный минус требует число");
    return r_none();
}

#endif /* RAMEEV_RUNTIME_H */

