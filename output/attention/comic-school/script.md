# The Message You Missed
*A football chat helps explain a new way to translate.*

Audience: **school**

**Key message:** Letting pieces of a sentence connect directly helped computers learn translation faster.

## Cast
- **Sam** (Football fan with an unread team chat): A 15-year-old boy with a lanky build, medium-brown skin, and short black curls. He wears a mustard-yellow hoodie, navy shorts, white socks, and muddy red football boots. His distinctive accessory is a black wristband with a small silver football charm.
- **Lea** (Curious friend who spots the useful connection): A 15-year-old girl with a stocky build, light olive skin, and a straight dark-brown bob. She wears a teal overshirt, plain white T-shirt, purple trousers, and white trainers. Her distinctive accessory is a bright orange, crescent-shaped hair clip.

## 1. Somewhere Above the Biscuit Debate

**Panel 1**
> Scene: At a university science fair, Sam and Lea stand centrally beside a plain demonstration table. Sam frowns at his phone, whose screen contains a tall stack of blank chat bubbles. Lea points toward an earlier bubble. A football rests between Sam’s muddy boots. Use a medium, eye-level view with uncluttered upper-left space.
- Sam: Where’s the match? Our team chat is enormous.
- Lea: The pitch update is above the biscuit argument.

**Panel 2**
> Scene: The table projects a central row of blank chat-bubble tiles, linked end to end. A single amber glow travels through one link while the remaining tiles stay dim. Sam leans close, impatiently tapping his wristband. Lea follows the chain with one finger. Keep the projection entirely free of symbols or writing.
- Caption: Older translation models often worked like a message passed down a line.
- Sam: Each step waits for the one before?
- Lea: Right. That makes learning harder to speed up.

**Panel 3**
> Scene: In a closer view, the projected blank tiles form a shallow arc at the centre. Glowing threads directly connect distant tiles, bypassing the intervening ones. Sam raises his eyebrows as Lea gestures across the arc. His phone sits beneath the projection, visually echoing its blank chat-bubble shapes. Leave the upper-left background clear.
- Caption: The paper’s big idea: let sentence pieces link up directly.
- Lea: Like finding the pitch update without passing through every argument.

**Panel 4**
> Scene: The central projection now has three differently coloured sets of threads connecting different blank tiles. Lea watches with an amused smile. Sam studies it seriously while retrieving a slightly crushed biscuit from his hoodie pocket. His football remains by his boots. Frame both teenagers from the waist up, with the biscuit clearly visible.
- Caption: Several sets of links can pick up different clues.
- Sam: Pitch update. Kit update. Biscuit update.
- Lea: You’ve found your priorities.

## 2. Faster Learning, Same Team Chat

**Panel 1**
> Scene: Sam and Lea stand at the plain science-fair table in a fresh, self-contained establishing view. Between them floats an arc of blank chat-bubble tiles joined by glowing threads. Sam holds his phone beside the projection, comparing their shapes. Lea rests one hand on the table. All surrounding stands are indistinct and unmarked.
- Caption: This translation design links sentence pieces like messages in a group chat.
- Sam: Okay. What does connecting the pieces change?

**Panel 2**
> Scene: A close view centres on the projected tiles, with many glowing simultaneously and threads stretching between them. Lea opens both hands toward the whole arrangement. Sam has pulled up a stool but stops halfway through sitting, looking pleasantly surprised. The tabletop holds only the phone and a football-shaped key dish, without markings.
- Caption: During training, many sentence pieces can be worked on together.
- Lea: It learned faster than earlier translation designs in the paper.
- Sam: Less waiting around. I approve.

**Panel 3**
> Scene: The projection shows connected blank tiles above a separate, emerging row below. Only the next tile in the lower row is materialising; empty space follows it. Lea points to that single new tile while Sam watches attentively. Keep the action central and the visual distinction between the connected input and growing output simple.
- Caption: Its best English-to-German result beat every earlier result they compared.
- Sam: Does it write the whole translation at once?
- Lea: No. It still writes one piece at a time.

**Panel 4**
> Scene: Sam stands centrally, offering his phone toward the impressive projection with exaggerated hope. Lea gently turns the phone back toward him, wearing a warm, deadpan expression. His muddy boots and football are visible below the table. A tiny biscuit crumb clings to his hoodie. Use a slightly wider view for the final reaction.
- Sam: Can it fix our team chat?
- Lea: Try reading the message first.

**Takeaway:** Computers can learn translation faster when sentence pieces connect directly, like messages in a group chat.

## Facts used (check these against the paper!)
- Earlier recurrent translation models computed states sequentially, with each position depending on the previous state. *(Section 1, Introduction.)*
- This sequential structure limited parallel computation within training examples. *(Section 1, Introduction.)*
- The Transformer uses attention rather than recurrence or convolution to relate sequence positions. *(Sections 2 and 3; Section 7, Conclusion.)*
- Encoder self-attention allows each position to attend directly to all positions in the preceding encoder layer, including distant positions. *(Section 3.2.3, Applications of Attention; Section 4 and Table 1.)*
- Multiple attention heads allow different sets of relationships to be considered in parallel. *(Section 3.2.2, Multi-Head Attention.)*
- Different attention heads can exhibit different patterns related to sentence structure. *(Section 4; appendix Figures 3–5.)*
- The Transformer permits more parallel processing during training and was trained faster than the earlier recurrent or convolutional translation architectures discussed. *(Section 1; Section 5.2; Section 7, Conclusion.)*
- The big Transformer’s English-to-German translation result exceeded the previously reported results compared in the paper, including ensembles. *(Section 6.1, Machine Translation; Table 2.)*
- The decoder generates its output one element at a time, using previously generated elements. *(Section 3, Model Architecture; Section 3.1, Decoder.)*
