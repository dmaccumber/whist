#include <pybind11/pybind11.h>
#include <pybind11/stl.h>
#include <cstdint>
#include <utility>
#include <cstring>

namespace py = pybind11;

static uint64_t SUIT_MASK[4];
// Zobrist random values for hashing
static uint64_t ZOBRIST_CARD[2][52];  // [player][card_id]
static uint64_t ZOBRIST_LEADER[2];
static uint64_t ZOBRIST_LEAD[53];     // [lead_id + 1] (lead_id is -1..51)

static void init_tables() {
    for (int s = 0; s < 4; s++) {
        uint64_t mask = 0;
        for (int r = 0; r < 13; r++)
            mask |= (1ULL << (r * 4 + s));
        SUIT_MASK[s] = mask;
    }
    // Initialize Zobrist values with a simple PRNG
    uint64_t state = 0xdeadbeefcafe1234ULL;
    auto next = [&]() -> uint64_t {
        state ^= state << 13; state ^= state >> 7; state ^= state << 17;
        return state;
    };
    for (int p = 0; p < 2; p++)
        for (int c = 0; c < 52; c++)
            ZOBRIST_CARD[p][c] = next();
    ZOBRIST_LEADER[0] = next();
    ZOBRIST_LEADER[1] = next();
    for (int i = 0; i < 53; i++)
        ZOBRIST_LEAD[i] = next();
}

// Fixed-size TT using Zobrist hashing
enum TTFlag : uint8_t { TT_EXACT = 0, TT_LOWER = 1, TT_UPPER = 2, TT_EMPTY = 3 };

struct TTEntry {
    uint64_t hash;      // Full hash for collision detection
    int16_t score;
    int8_t best_card;
    TTFlag flag;
};

static constexpr int TT_SIZE_BITS = 22;  // 4M entries
static constexpr int TT_SIZE = 1 << TT_SIZE_BITS;
static constexpr int TT_MASK = TT_SIZE - 1;

static TTEntry g_tt[TT_SIZE];

static inline uint64_t compute_hash(uint64_t hand0, uint64_t hand1, int leader, int lead_id) {
    uint64_t h = ZOBRIST_LEADER[leader] ^ ZOBRIST_LEAD[lead_id + 1];
    uint64_t m = hand0;
    while (m) { int bit = __builtin_ctzll(m); h ^= ZOBRIST_CARD[0][bit]; m &= m - 1; }
    m = hand1;
    while (m) { int bit = __builtin_ctzll(m); h ^= ZOBRIST_CARD[1][bit]; m &= m - 1; }
    return h;
}

static inline void iter_bits_desc(uint64_t mask, int* out, int& count) {
    count = 0;
    while (mask) {
        uint64_t lsb = mask & (-mask);
        out[count++] = __builtin_ctzll(lsb);
        mask ^= lsb;
    }
    for (int i = 0; i < count / 2; i++) {
        int tmp = out[i]; out[i] = out[count-1-i]; out[count-1-i] = tmp;
    }
}

static inline void iter_bits_asc(uint64_t mask, int* out, int& count) {
    count = 0;
    while (mask) {
        uint64_t lsb = mask & (-mask);
        out[count++] = __builtin_ctzll(lsb);
        mask ^= lsb;
    }
}

static inline void prioritize_move(int* moves, int count, int best_move) {
    if (best_move < 0 || count <= 1) return;
    for (int i = 1; i < count; i++) {
        if (moves[i] == best_move) {
            int tmp = moves[0]; moves[0] = moves[i]; moves[i] = tmp;
            return;
        }
    }
}

static int ab_exact(
    uint64_t hand0, uint64_t hand1,
    int trump, int leader, int lead_id,
    int alpha, int beta,
    int* best_card_out,
    int depth_remaining  // For iterative deepening: -1 = full, >=0 = limited
) {
    if (hand0 == 0 && hand1 == 0) { *best_card_out = -1; return 0; }
    if (lead_id < 0 && (hand0 == 0 || hand1 == 0)) { *best_card_out = -1; return 0; }

    // Depth-limited: evaluate as 0 (draw estimate) for ID warmup
    if (depth_remaining == 0 && lead_id < 0) {
        *best_card_out = -1;
        // Quick estimate: count top cards for each player
        uint64_t all = hand0 | hand1;
        int est = 0;
        for (int s = 0; s < 4; s++) {
            uint64_t suit = all & SUIT_MASK[s];
            while (suit) {
                int top = 63 - __builtin_clzll(suit);
                if (hand0 & (1ULL << top)) est++;
                else break;
                suit ^= (1ULL << top);
            }
        }
        return est;
    }

    uint64_t hash = compute_hash(hand0, hand1, leader, lead_id);
    int tt_idx = (int)(hash & TT_MASK);
    int tt_best_move = -1;

    TTEntry& te = g_tt[tt_idx];
    if (te.flag != TT_EMPTY && te.hash == hash) {
        tt_best_move = te.best_card;
        if (depth_remaining < 0) {  // Only use TT cutoffs in full search
            if (te.flag == TT_EXACT) {
                *best_card_out = te.best_card;
                return te.score;
            } else if (te.flag == TT_LOWER) {
                if (te.score >= beta) { *best_card_out = te.best_card; return te.score; }
                if (te.score > alpha) alpha = te.score;
            } else if (te.flag == TT_UPPER) {
                if (te.score <= alpha) { *best_card_out = te.best_card; return te.score; }
                if (te.score < beta) beta = te.score;
            }
        }
    }

    int orig_alpha = alpha;
    int card_ids[13];
    int n_cards;
    int best_cid, best_score;
    int next_depth = (depth_remaining > 0) ? depth_remaining - 1 : depth_remaining;

    if (lead_id < 0) {
        int current = leader;
        uint64_t legal = (current == 0) ? hand0 : hand1;
        bool maximizing = (current == 0);

        iter_bits_desc(legal, card_ids, n_cards);
        prioritize_move(card_ids, n_cards, tt_best_move);

        best_score = maximizing ? -1 : 14;
        best_cid = card_ids[0];

        for (int i = 0; i < n_cards; i++) {
            int cid = card_ids[i];
            uint64_t bit = 1ULL << cid;
            uint64_t h0 = (current == 0) ? (hand0 ^ bit) : hand0;
            uint64_t h1 = (current == 1) ? (hand1 ^ bit) : hand1;

            int child_best;
            int score = ab_exact(h0, h1, trump, leader, cid, alpha, beta, &child_best, next_depth);

            if (maximizing) {
                if (score > best_score) { best_score = score; best_cid = cid; }
                if (score > alpha) alpha = score;
            } else {
                if (score < best_score) { best_score = score; best_cid = cid; }
                if (score < beta) beta = score;
            }
            if (beta <= alpha) break;
        }
    } else {
        int follower = 1 - leader;
        uint64_t hand = (follower == 0) ? hand0 : hand1;
        int led_suit = lead_id & 3;
        uint64_t in_suit = hand & SUIT_MASK[led_suit];
        uint64_t legal = in_suit ? in_suit : hand;
        bool maximizing = (follower == 0);
        int lead_rank_idx = lead_id >> 2;

        // Order: winners first (ascending), then losers (ascending)
        int winners[13], losers[13]; int nw = 0, nl = 0;
        {
            int all[13]; int na;
            iter_bits_asc(legal, all, na);
            for (int i = 0; i < na; i++) {
                int cid = all[i];
                int fs = cid & 3, fr = cid >> 2;
                bool wins = (fs == led_suit) ? (fr > lead_rank_idx) : (fs == trump);
                if (wins) winners[nw++] = cid; else losers[nl++] = cid;
            }
        }
        n_cards = 0;
        for (int i = 0; i < nw; i++) card_ids[n_cards++] = winners[i];
        for (int i = 0; i < nl; i++) card_ids[n_cards++] = losers[i];
        prioritize_move(card_ids, n_cards, tt_best_move);

        best_score = maximizing ? -1 : 14;
        best_cid = card_ids[0];

        for (int i = 0; i < n_cards; i++) {
            int cid = card_ids[i];
            int follow_suit = cid & 3, follow_rank_idx = cid >> 2;
            int winner_offset;
            if (follow_suit == led_suit)
                winner_offset = (lead_rank_idx > follow_rank_idx) ? 0 : 1;
            else if (follow_suit == trump)
                winner_offset = 1;
            else
                winner_offset = 0;

            int trick_winner = leader ^ winner_offset;
            int bonus = (trick_winner == 0) ? 1 : 0;

            uint64_t bit = 1ULL << cid;
            uint64_t h0 = (follower == 0) ? (hand0 ^ bit) : hand0;
            uint64_t h1 = (follower == 1) ? (hand1 ^ bit) : hand1;

            int child_best;
            int sub = ab_exact(h0, h1, trump, trick_winner, -1, alpha, beta, &child_best, next_depth);
            int score = sub + bonus;

            if (maximizing) {
                if (score > best_score) { best_score = score; best_cid = cid; }
                if (score > alpha) alpha = score;
            } else {
                if (score < best_score) { best_score = score; best_cid = cid; }
                if (score < beta) beta = score;
            }
            if (beta <= alpha) break;
        }
    }

    // Store in TT (always replace — simple replacement policy)
    if (depth_remaining < 0) {
        TTFlag flag;
        if (best_score <= orig_alpha) flag = TT_UPPER;
        else if (best_score >= beta) flag = TT_LOWER;
        else flag = TT_EXACT;
        te = {hash, (int16_t)best_score, (int8_t)best_cid, flag};
    } else {
        // ID warmup: store best move but mark as non-exact
        te = {hash, (int16_t)best_score, (int8_t)best_cid, TT_LOWER};
    }

    *best_card_out = best_cid;
    return best_score;
}

std::pair<int, int> solve(uint64_t hand0, uint64_t hand1, int trump, int leader, int lead_id) {
    // Clear TT
    for (int i = 0; i < TT_SIZE; i++) g_tt[i].flag = TT_EMPTY;

    int best_card;

    // Iterative deepening warmup: 4, 8, 12 plies, then full
    for (int depth : {4, 8, 12}) {
        ab_exact(hand0, hand1, trump, leader, lead_id, 0, 14, &best_card, depth);
    }

    // Full search with TT populated from warmup
    int score = ab_exact(hand0, hand1, trump, leader, lead_id, 0, 14, &best_card, -1);
    return {score, best_card};
}

PYBIND11_MODULE(_minimax_cpp, m) {
    init_tables();
    m.doc() = "C++ minimax solver for German Whist Phase 2";
    m.def("solve", &solve,
          py::arg("hand0"), py::arg("hand1"), py::arg("trump"),
          py::arg("leader"), py::arg("lead_id"));
}
