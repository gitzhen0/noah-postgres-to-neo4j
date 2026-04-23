# Neo4j Browser Demo Cheat Sheet — Slide 7

The "empty → full" demo depends on having a Neo4j Browser tab open alongside
the deck. This sheet is the exact sequence to follow.

Open once before the defense, paste commands into Favorites, then during the
demo you only need **up-arrow + Enter**.

---

## Tab setup (5 min before going live)

1. Open Chrome tab at `http://localhost:7474`
2. Login: `neo4j` / `password123` (database: `neo4j`)
3. Click the ⭐ icon in the left sidebar → "Add to favorites" for each of the
   queries below, one by one. Name them clearly so you can click them live.

---

## The 4 queries (save as Favorites, in this order)

### ① Clear (run once, right before the demo starts)

```cypher
MATCH (n) DETACH DELETE n;
```

> Wipes everything. Confirm with a count query after — must say 0.

### ② Count (this is what you run on camera)

```cypher
MATCH (n) RETURN count(n) AS total_nodes;
```

> Big number in the center of the screen. Runs in <100 ms. Use this one
> both **before** migrate (shows `0`) and **after** migrate (shows `11183`).

### ③ Visualize (the "wow" query after the count jumps to 11,183)

```cypher
MATCH (n) RETURN n LIMIT 100;
```

> Pops up a colorful graph. Takes ~1 second to render. The node colors map to
> labels: HousingProject (blue) · ZipCode (teal) · Demographic (green) ·
> Affordability (amber) · RentBurden (red).

### ④ Traversal proof (backup in case Fortino asks "show me a multi-hop query")

```cypher
MATCH path = (z:ZipCode {zip_code:'10001'})-[:NEIGHBORS*0..2]-(n)
RETURN path LIMIT 30;
```

> Same query as slide 13 Hero. Shows the variable-length traversal visually.

---

## On-stage choreography

| When | Tab | Action | Expected |
|---|---|---|---|
| Slide 6 finishes | deck | Advance to slide 7 | — |
| — | Neo4j Browser | Click Favorite ② (count) | **total_nodes: 0** |
| — | deck | Read the "Step 1" cue aloud | — |
| — | deck → terminal | `python main.py migrate` | ~8 s, 11,183 nodes |
| — | terminal | `python main.py audit` | PASS, ~1.3 s |
| — | Neo4j Browser | Up-arrow + Enter (reruns count) | **total_nodes: 11183** |
| — | Neo4j Browser | Click Favorite ③ (LIMIT 100) | colorful graph renders |
| — | deck | Advance to slide 8 (audit table) | — |

Total stage time: ~2.5 min. Leaves 30 s buffer for "wait did it really just do that?" beat.

---

## If things go sideways

**Neo4j Browser won't load / shows connection error**
→ `docker restart noah-neo4j-restored`. Wait 15 s. Refresh the tab.

**Count query returns > 0 before Step 1**
→ You forgot to clear. Paste Favorite ① first, then Favorite ②.

**Migration hangs partway**
→ Ctrl-C, `docker logs --tail 20 noah-neo4j-restored`, rerun. It's idempotent
— MERGE will skip what's already there.

**Browser viz shows no nodes even though count=11,183**
→ You're looking at a cached empty canvas. Hit the refresh icon in the Neo4j
Browser result pane, or rerun Favorite ③.

**Chrome won't open localhost:7474 (CORS/Frame error)**
→ Only happens if you changed neo4j.conf. Out-of-box install works fine.
