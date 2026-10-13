# Dashboard Design: The Krusty Krab Ops Board

The Campus Customs agent team, re-staged as the Krusty Krab crew. The dashboard lives in `frontend/` (Vite + React + TypeScript), runs with `npm run dev` on **http://localhost:5181**, and talks only to the FastAPI backend on **http://localhost:8000**.

The goal: a manager should be able to glance at the board and know **which tickets are done, who is working, what they just said, what's waiting on them, and how much cash is left**, and enjoy doing it.

---

## 1. The cast: why each character plays each agent

| Agent | Character | Why this casting works |
|---|---|---|
| **Boss** | **Mr. Krabs** | He owns the restaurant, makes every final call, and obsesses over every penny. That's exactly the Boss's job: delegate, then decide what money goes out. |
| **Accounting** | **Squidward** | He's literally the Krusty Krab's cashier, and he handles the till. Accounting checks cash, files payment and purchase requests and prices discounts. |
| **Inventory** | **SpongeBob** | The fry cook who knows every patty in the back. Eager, fast and detail-obsessed, the right energy for counting stock and chasing vendor dates. |
| **Facilities** | **Sandy** | The scientist and engineer who built her own treedome. She's the natural owner of the shop space, the lease and "verify that notice, partner." |
| **Customer Service** | **Patrick** | The friendliest face in Bikini Bottom. He drafts the warm messages to customers, which are never sent without a human. |
| *(payment approved)* | **Plankton** | Always scheming to get into the Krabs vault. He dashes across the screen whenever money leaves, which is funny and a clear signal. |
| *(purchase approved)* | **Gary** | Slow, steady and leaves a trail. A restock purchase is a slow-moving thing (it arrives in `lead_days`), and the slime literally shows "something is on its way." |

Every character is **drawn in code as SVG** (`components/Characters.tsx`). There are no image files, so they stay crisp at any size, load instantly, and can be animated individually.

---

## 2. Layout

```
┌──────────────────────────────────────────────────────────────────────────────┐
│ 🦀 The Krusty Krab Ops Board   [2/3 resolved] [1 waiting on you] [💰 $3,400]  🔄 │  ← wooden sign top bar
├──────────────┬───────────────────────────────────────────┬───────────────────┤
│ ORDER BOARD  │ THE CREW                                  │ NEEDS YOUR OK  (2)│
│ ┌──────────┐ │  Krabs  SpongeBob  Squidward  Sandy  Pat  │ Approving as [__] │
│ │ #101  ✓  │ │  (active one lifts, glows, talks)         │ 📄 Invoice  $840  │
│ └──────────┘ │  speech bubble under each character       │  [✓ Approve][Rej] │
│ ┌──────────┐ ├───────────────────────────────────────────┤ 🛒 Purchase  $8   │
│ │ #102     │ │ KITCHEN RADIO (live feed)                 ├───────────────────┤
│ └──────────┘ │  🦀 Krabs: got a task …                   │ SHIFT REPORT      │
│ ┌──────────┐ │    🧽 SpongeBob: 🔍 Checked the stockroom │ Krabs' final call │
│ │ #103     │ │      🦑 Squidward: 💰 Prepared a payment  │ one card / agent  │
│ └──────────┘ │  🏁 Ticket wrapped up: waiting_approval   │ tools · handoffs  │
│ [🦀 Send in the crew]                                    │                   │
└──────────────┴───────────────────────────────────────────┴───────────────────┘
```

**Three columns that follow how the work actually flows, left to right:**

1. **Order Board (left): what needs doing.** The three tickets are drawn as **pinned paper order slips** on a wooden board, like a real diner rail, each slightly tilted. One click selects a slip, and one big red button sends in the crew. The board is sticky, so it stays in view while you scroll the feed.
2. **The Crew and the Kitchen Radio (center): what's happening now.** The crew line-up sits on a little sea-floor stage. Underneath, the live feed narrates every step of the run. This is the widest column because it's where the eye should be during a run.
3. **Needs Your OK and the Shift Report (right): what's waiting on you, and what got done.** Human decisions and results sit together, so the place to act and the outcome you're acting on are side by side.

**The top bar is a wooden Krusty Krab sign.** It holds the three numbers a manager always wants: tickets resolved, items waiting on them, and the checking balance in Mr. Krabs' treasure chest. **Fresh shift** (reset) lives here, behind a confirmation dialog.

**Responsive:** below 1250px the right column drops under the other two and splits into two side-by-side panels; below 820px everything stacks into one column, with the crew in a 3- or 2-across grid.

---

## 3. How the agents read differently

Each agent has its **own color, its own animated character, and its own "voice" in type**, so you can tell who is talking without reading the name.

| Agent | Accent | How its lines read | Why |
|---|---|---|---|
| Mr. Krabs | Krabby red | **Bold**, on a pale red bubble | He's the boss; his lines are decisions and should carry weight. |
| SpongeBob | Sponge yellow | **Semi-bold**, bright yellow bubble | Eager and upbeat, like the character. |
| Squidward | Teal | *Serif italic*, cool mint bubble | Squidward's weary, "cultured" monotone, and it makes money lines easy to spot. |
| Sandy | Acorn brown | `Monospace`, on a tan "lab notebook" bubble | The scientist voice: lease dates and figures line up like measurements. |
| Patrick | Starfish pink | Larger text in an extra-round bubble | Soft and friendly, matching customer messages. |

**On the stage**, the agent currently working **lifts up, glows in its own color, and does a "talking" wiggle**, while its speech bubble updates with its latest line or tool. Agents that haven't been involved are dimmed; finished agents get a green ✓ badge. You can watch the baton pass from Krabs to SpongeBob to Squidward and back.

**In the Kitchen Radio feed**, every line has the character's avatar, a colored left edge, and a tag (*got a task*, *used a tool*, *handed off*, *reports back*, *final call*). Lines from delegated agents are **indented by delegation depth**, so `Boss → Inventory → Accounting` reads as a visible chain. Raw tool names become plain language (`check_restock` → "🔍 Checked the stockroom", `pay_bill` → "💰 Prepared a payment"), with a **"Show tool call"** toggle for the exact arguments and result. Tool calls that touch **money, pricing, customer messages or tickets** get a colored flag, the same `sensitive` flag written to the audit trail.

When a character is handed a task, they open with an in-character line ("I'm ready! I'm ready! To the stockroom!"). **Those are the only invented words on the screen.** Every number, date, SKU and summary below them comes straight from the backend.

---

## 4. How resolved tickets show up

- **Open:** a blue *Open* pill on a plain slip.
- **Running:** the slip pulses with a **yellow glow** and the pill reads *● Crew working*, with a live dot. The run button becomes *Crew is on it…* with a spinner, and every other run is locked, so two runs can't spend the same cash.
- **Resolved:** when the run finishes, the slip turns pale green, gets a ✓ *Resolved* pill, and a big green **DONE stamp** slams onto it with a bounce. Underneath, an **outcome tag** keeps Mr. Krabs' honest verdict: *All done*, *Waiting on your OK*, *Blocked* or *Needs a human*. "The crew finished" and "the work is fully done" are different things, and the board shows both.
- A toast confirms it ("Ticket #101 done: Mr. Krabs says waiting_approval"). The **Shift Report** fills in with Mr. Krabs' final call (with a "Why" toggle for his reasoning) and **one card per crew member** who worked the ticket: their final summary, the tools they used as chips, who they handed work to, and the tokens they spent.
- The header counter (*2/3 tickets resolved*) ticks up.

---

## 5. How cash and approvals show up

- **The treasure chest** in the top bar always shows the live `checking` balance from `cash_accounts`, with the shop's date.
- When money leaves, the balance **counts down smoothly** instead of jumping, the chest **flashes gold**, and a red **−$840.00** floats up and fades. You see *that* it changed, *by how much*, and *what it is now*.
- **Needs Your OK** lists every payment and purchase the agents prepared, each with its amount, plain-language reason, who requested it and its approval number. Green-edged cards are payments and pink-edged cards are purchases, matching the character who'll celebrate them. A **coverage check** sums everything waiting and warns in red if it's more than the till holds ("$104.00 more than the till holds. Some will be refused.").
- **Approve & pay** is disabled until you type your name, because the payment log records who approved it. The name is remembered for next time.
- **On approval:**
  - **Payments** (invoice or rent): a banner drops in and **Plankton scurries across the screen** with a trail of **bubbles** rising behind him.
  - **Purchases** (restock orders): **Gary slides across slowly**, leaving a glistening **green slime trail** that oozes out behind him, and says "Meow."
- **If the backend refuses** (for example, Gary's purchase while the vendor is still blocked by an unpaid invoice, or anything that would overdraw the account), there's no celebration. A red toast explains exactly why, in the backend's own words.
- **Recent decisions** shows the ledger: what was paid, by whom, what was rejected, and which restocks are on order with their arrival date.

---

## 6. Why these choices make it feel special, and easy to use

**Special:**
- **A world, not a template.** The ocean backdrop has drifting light rays, rising bubbles and sea-flower silhouettes. The panels have thick cartoon outlines and offset shadows, and the headings use the bubbly *Luckiest Guy* display font. Together they make it feel like an episode of the show rather than an admin panel.
- **Characters who act.** The crew bobs while idle, wiggles while talking and earns check marks. Agent work stops being an invisible API call and becomes something you watch happen.
- **Celebrations tied to meaning.** Plankton and Gary only appear on real money events, so the animation reinforces *what* happened (payment vs. purchase). It isn't decoration for its own sake.

**User-friendly:**
- **Left-to-right flow** (pick → watch → approve/review) mirrors the task, so there's never a question of where to look next.
- **The three numbers that matter are always visible:** tickets done, items waiting on you, cash left.
- **Everything has a human label:** tool names in plain English, outcomes in plain English, amounts in dollars, dates from the shop's own calendar. Raw details are one click away for auditing.
- **Guardrails are visible, not hidden:** approval needs your name, reset needs confirmation, runs are one at a time, and the coverage check warns before you approve more than the till holds.
- **Live without refreshing:** the board polls every 4 seconds, and every second during a run. A refreshed page picks a run back up from the audit trail. If the backend is down, a banner says exactly which command starts it.
- **Accessible:** real buttons and listbox semantics, visible yellow focus rings, `aria-live` regions for the feed, toasts and balance, a skip link, high-contrast ink on parchment, and **`prefers-reduced-motion` support** that turns off the parades and bubbles for anyone who needs calm screens.

---

## 7. What talks to what

| UI piece | Backend route |
|---|---|
| Order Board | `GET /api/tickets` (open, running or resolved, plus the Boss's outcome) |
| Send in the crew | `POST /api/tickets/{id}/run` → `run_id` |
| Crew stage and Kitchen Radio | `GET /api/events?run_id=…` (every second during a run) and `GET /api/runs/{run_id}` |
| Shift Report | `GET /api/tickets/{id}/summary` |
| Needs Your OK | `GET /api/approvals`, `POST /api/approvals/{id}/approve`, `POST /api/approvals/{id}/reject` |
| Recent decisions (orders) | `GET /api/purchase-orders` |
| Treasure chest | `GET /api/cash` |
| Fresh shift | `POST /api/reset` |
