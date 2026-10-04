/* Multi-layer grid A* for scripts/pcbgen/grid_router.py (loaded through ctypes).
 * Same semantics as the Python astar(): 8-connected planar moves without
 * corner cutting, per-cell cost multipliers, layer changes at via-legal or
 * through-copper cells. Returns the path length or -1. */
#include <float.h>
#include <math.h>
#include <stdint.h>
#include <stdlib.h>

typedef struct { float f; int32_t i; } item;
typedef struct { item *a; long n, cap; } heap;

static int push(heap *h, float f, int32_t i) {
    if (h->n == h->cap) {
        long cap = h->cap ? h->cap * 2 : 1 << 16;
        item *a = realloc(h->a, cap * sizeof(item));
        if (!a) return 0;
        h->a = a; h->cap = cap;
    }
    long k = h->n++;
    while (k > 0) {
        long p = (k - 1) / 2;
        if (h->a[p].f <= f) break;
        h->a[k] = h->a[p]; k = p;
    }
    h->a[k].f = f; h->a[k].i = i;
    return 1;
}

static item pop(heap *h) {
    item top = h->a[0], last = h->a[--h->n];
    long k = 0;
    for (;;) {
        long c = 2 * k + 1;
        if (c >= h->n) break;
        if (c + 1 < h->n && h->a[c + 1].f < h->a[c].f) c++;
        if (last.f <= h->a[c].f) break;
        h->a[k] = h->a[c]; k = c;
    }
    if (h->n) h->a[k] = last;
    return top;
}

long grid_astar(int L, int H, int W, const uint8_t *passable, const float *cost,
                const uint8_t *via_ok, const uint8_t *through, const uint8_t *src,
                const uint8_t *goal, const float *hdist, const float *via_cost, long max_exp,
                int32_t *out, long cap, long *expanded) {
    long plane = (long)H * W, total = plane * L, found = -1, n = 0;
    float *g = malloc(total * sizeof(float));
    int32_t *prev = malloc(total * sizeof(int32_t));
    heap h = {0};
    if (!g || !prev) { free(g); free(prev); return -2; }
    for (long i = 0; i < total; i++) { g[i] = FLT_MAX; prev[i] = -1; }
    for (long i = 0; i < total; i++)
        if (src[i]) { g[i] = 0; if (!push(&h, hdist[i % plane], (int32_t)i)) goto done; }
    static const int dy[8] = {-1, 1, 0, 0, -1, -1, 1, 1}, dx[8] = {0, 0, -1, 1, -1, 1, -1, 1};
    static const float step[8] = {1, 1, 1, 1, 1.41421356f, 1.41421356f, 1.41421356f, 1.41421356f};
    *expanded = 0;
    while (h.n) {
        item t = pop(&h);
        long i = t.i, l = i / plane, rest = i % plane, y = rest / W, x = rest % W;
        float gi = g[i];
        if (t.f - hdist[rest] > gi + 1e-4f) continue;
        if (++*expanded > max_exp) break;
        if (goal[i]) { found = i; break; }
        for (int k = 0; k < 8; k++) {
            long ny = y + dy[k], nx = x + dx[k];
            if (ny < 0 || ny >= H || nx < 0 || nx >= W) continue;
            long j = l * plane + ny * W + nx;
            if (!passable[j]) continue;
            if (k >= 4 && !(passable[l * plane + y * W + nx] && passable[l * plane + ny * W + x])) continue;
            float ng = gi + step[k] * cost[j];
            if (ng < g[j]) { g[j] = ng; prev[j] = (int32_t)i; if (!push(&h, ng + hdist[ny * W + nx], (int32_t)j)) goto done; }
        }
        if (through[rest] || via_ok[rest]) {
            float c = through[rest] ? 0.5f : via_cost[rest];
            for (long l2 = 0; l2 < L; l2++) {
                long j = l2 * plane + rest;
                if (l2 == l || !passable[j]) continue;
                float ng = gi + c;
                if (ng < g[j]) { g[j] = ng; prev[j] = (int32_t)i; if (!push(&h, ng + hdist[rest], (int32_t)j)) goto done; }
            }
        }
    }
    if (found >= 0) {
        for (long i = found; i >= 0; i = prev[i]) { if (n < cap) out[n] = (int32_t)i; n++; }
        if (n > cap) n = -3;
    }
done:
    free(g); free(prev); free(h.a);
    return found >= 0 ? n : -1;
}
