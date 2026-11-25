# The End of the Office Relay
*How the Transformer changed the economics of training translation systems—not the need for business judgement.*

Audience: **business**

**Key message:** The Transformer removed a sequential training bottleneck, improving translation quality with less training computation; business value still needs testing.

## Cast
- **Ingrid** (Operations director asking where the business value lies): A 52-year-old woman with a sturdy build, fair skin, and a straight silver-blonde bob tucked behind one ear. She wears a navy trouser suit, ivory blouse, and burgundy loafers. Her distinctive accessory is a chunky amber brooch on her left lapel.
- **Ravi** (Process improvement lead explaining the research): A 38-year-old man with a lean build, medium-brown skin, short curly black hair, and a neatly trimmed beard. He wears a moss-green blazer, pale-blue open-collar shirt, charcoal trousers, and brown shoes. His distinctive accessory is a round orange watch.

## 1. The bottleneck, then the breakthrough

**Panel 1** (wide)
> Scene: An eye-level establishing view of a conference lounge with tall windows and a distant warehouse roofline. Ingrid and Ravi stand centrally beside a small round table, holding plain coffee cups. Ingrid raises one eyebrow; Ravi opens a blank folder. Leave generous empty wall space in the upper-left corner. All surfaces are unmarked.
- Caption: A conference coffee break. Ingrid has one question the board will recognise.
- Ingrid: What changed here: the quality, the cost, or just the presentation?
- Ravi: Quality and training efficiency. For once, the presentation is not the breakthrough.

**Panel 2**
> Scene: A three-quarter overhead view of a tabletop process model between Ingrid and Ravi. A long chain of miniature desks carries identical blank tiles. Only one central desk glows; the remaining desks are dim. Ingrid studies the chain with weary recognition while Ravi points along its route. Keep the model centred and the upper-left background clear.
- Caption: Many leading language systems processed a sentence in sequence. During training, each position depended on the previous step.
- Ingrid: A process where every desk waits for the desk before it. We have those.

**Panel 3** (wide)
> Scene: The tabletop model has opened into a broad circular review table covered with blank tiles. Fine luminous threads connect tiles across the centre, including widely separated ones. Ravi gestures towards the direct connections while Ingrid leans forward with cautious interest. The old miniature desk chain sits folded at the far edge. No markings appear anywhere.
- Caption: The paper’s Transformer replaced that sequence-by-sequence processing with attention: direct connections between positions, without recurrent or convolutional layers.
- Ravi: Think shared review table, rather than a relay. Each piece can draw information directly from the others.
- Ingrid: An all-hands meeting with a defensible purpose. Bold.

**Panel 4**
> Scene: Close view across the shared table, with Ingrid and Ravi visible behind it. Several translucent streams flow from blank tiles into one central tile. Stream widths vary clearly, and their colours blend at the destination. Ravi holds an open palm above the arrangement. Ingrid gives him a dry sideways glance. Leave the upper-left area uncluttered.
- Caption: Attention mixes information from other positions, giving more weight to what matches the current position’s needs.
- Ravi: Not every contribution gets equal weight. The system learns which connections are useful.
- Ingrid: So, unlike the budget meeting.

**Panel 5**
> Scene: A centred tabletop close-up shows several differently coloured glass lenses suspended over an ordered row of blank tiles. Each lens reveals a different pattern of connecting threads. Beneath the tiles run smooth coloured waves with varying phases. Ingrid keeps the row aligned with one hand while Ravi adjusts a lens. The background remains plain and unmarked.
- Caption: Several attention heads provide different views at once. Added position signals preserve information about the order of the pieces.
- Ravi: Several review lenses, plus a way to retain order—not just a bag of sentence pieces.

**Panel 6**
> Scene: Ingrid and Ravi stand behind a compact machine model. On its left, many blank tiles glow simultaneously across a broad tray. On its right, a narrow outlet delivers a single tile towards a short existing row. An opaque cover conceals the remaining outlet path. Ravi indicates the contrast while Ingrid watches carefully. Keep the main mechanism centred.
- Caption: Training can handle positions in parallel. Producing a translation still proceeds one piece at a time.
- Ingrid: Faster training does not mean the finished translation appears all at once?
- Ravi: Correct. It still builds the answer in order, without peeking at future pieces.

## 2. Results, not a business case

**Panel 1** (wide)
> Scene: A frontal view shows Ingrid and Ravi beside a minimalist comparison sculpture on the coffee table. A single tall column stands next to a shorter column assembled from several slender pieces. Neither has ticks or labels. Ravi presents the taller column; Ingrid examines both with folded arms. The upper-left wall is empty, with all numerical information reserved for captions.
- Caption: On the WMT 2014 English-to-German translation test, the larger Transformer scored 28.4, versus 26.36 for the strongest previously reported result.
- Ravi: Higher is better on this translation measure. It beat even the previous combination of several models.
- Ingrid: Better output. A useful opening argument.

**Panel 2**
> Scene: A slightly elevated view shows two model configurations on a central display table: a compact stack of plain blocks and a substantially larger stack. Behind them sits one shared rack of identical unmarked computing units. Ravi gestures between the configurations while Ingrid balances her coffee cup on its saucer. No clocks, figures, logos, or labels are visible.
- Caption: Both configurations trained on eight graphics processors. The paper also reported lower estimated training computation than competing systems.
- Ravi: The smaller model trained in 12 hours and scored 27.3. The larger took 3.5 days and scored 28.4.
- Ingrid: Different budgets, different quality. Now it sounds like an actual purchasing discussion.

**Panel 3**
> Scene: The shared review table now extends far into the room, crowded with blank tiles and a dense web of connecting threads. The web remains inside the tabletop boundary rather than touching the people. Ingrid and Ravi stand centrally at its near edge, looking at the expanding arrangement with sober expressions. Leave the upper-left wall clear.
- Caption: There is a trade-off: comparing every position with every other position becomes costly as sequences grow longer.
- Ingrid: So inviting the whole document to the meeting is not free.
- Ravi: Exactly. The paper proposed investigating more local connections for very long sequences.

**Panel 4**
> Scene: Ingrid and Ravi stand at a central workbench holding a small polished engine-like model. Across an open gap sits a detailed miniature warehouse with loading bays and delivery vehicles. No bridge connects the bench to the warehouse. Ingrid points towards the gap while Ravi nods. All buildings, vehicles, papers, and clothing are free of lettering or symbols.
- Caption: The experiments covered machine translation and English sentence-structure analysis—not company profits, operational savings or deployment risk.
- Ingrid: Evidence for a better technical engine. Not evidence that it can run my operations.
- Ravi: Precisely. The paper did not test your business case.

**Panel 5**
> Scene: A three-quarter view shows Ingrid and Ravi seated at the coffee table, now working together. Ingrid places a small, bounded tray of blank documents beside a larger untouched stack. Ravi arranges a stopwatch without dial markings, plain coins, and a magnifying glass beside the tray. A closed laptop rests farther away. Their expressions are practical and focused.
- Caption: For Ingrid, the next step is a proposed pilot—not a conclusion from the paper.
- Ingrid: Test one document workflow. Compare turnaround, total cost and errors with today’s process. Keep human approval.
- Ravi: And agree the success criteria before the demonstration develops a personality.

**Panel 6** (wide)
> Scene: A wide closing view returns to the conference lounge. Ingrid closes the blank folder and stands with a composed, decisive expression. Ravi gathers their empty cups. The small pilot tray remains centred on the table, while the elaborate process models sit farther behind them. Daylight falls across the scene. Leave ample clean space in the upper-left corner.
- Caption: The breakthrough removed a training bottleneck. The business decision still needs its own evidence.
- Ingrid: A better engine is a reason to test—not a reason to sign a blank cheque.
- Ravi: That should fit on the board agenda.

**Takeaway:** This research made language systems more practical to train; our investment case still needs measured quality, cost and risk.

## Facts used (check these against the paper!)
- Many leading sequence models used recurrent processing, whose dependence on previous positions prevented parallel computation across positions within a training example. *(Paper, Section 1.)*
- The Transformer dispensed with recurrence and convolution, using attention mechanisms alongside position-wise feed-forward layers. *(Paper, Abstract; Sections 2 and 3.)*
- Encoder self-attention permits each position to attend to every position in the preceding encoder layer, providing direct connections across distant positions. *(Paper, Section 3.2.3; Section 4 and Table 1.)*
- Attention outputs a weighted sum of values, with weights determined by compatibility between queries and keys; the model uses learned projections. *(Paper, Sections 3.2, 3.2.1 and 3.2.2.)*
- Multi-head attention allows simultaneous attention to different representation subspaces and positions. *(Paper, Section 3.2.2.)*
- Positional encodings are added to embeddings to supply sequence-order information. *(Paper, Section 3.5.)*
- The Transformer enables more parallel computation during training, but its decoder generates output autoregressively, one element at a time. *(Paper, Sections 1, 3 and 4.)*
- Decoder masking and shifted output embeddings ensure predictions depend only on known preceding outputs, not future outputs. *(Paper, Section 3.1.)*
- On WMT 2014 English-to-German newstest2014, Transformer (big) scored 28.4 BLEU, compared with 26.36 for the strongest previously reported result listed, the ConvS2S ensemble. *(Paper, Table 2 and Section 6.1.)*
- BLEU is a translation evaluation measure for which higher scores indicate better agreement with reference translations. *(General knowledge, not from the paper; the paper reports BLEU results in Table 2.)*
- The base Transformer scored 27.3 BLEU on the same English-to-German test. *(Paper, Table 2.)*
- Base models trained for 12 hours and big models for 3.5 days on a machine with eight NVIDIA P100 graphics processors. *(Paper, Section 5.2; Section 6.1 confirms the English-to-German big model's training duration.)*
- The paper reports lower estimated training computation than competing translation systems, estimating training cost from duration, processor count and sustained floating-point capacity. *(Paper, Table 2 and Section 6.1.)*
- Full self-attention compares all positions and has per-layer computational complexity quadratic in sequence length. *(Paper, Table 1 and Section 4.)*
- The authors proposed investigating restricted, local attention to improve computational performance on very long sequences. *(Paper, Sections 4 and 7.)*
- The reported experiments concern machine translation and English constituency parsing, not company profitability, operational savings or deployment-risk evaluation. *(Paper, Sections 6.1–6.3; scope of the reported experiments.)*
