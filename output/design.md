# Dashboard look

The desk is a Yale paper, not a generic app skin. The page color is limestone (`#f4efe6`) with Yale blue (`#00356b`) for the title, the ticket rule, and the checking block. Type is Libre Baskerville for the title, the balance, and the agents' thoughts, and Source Sans 3 for the rest of the desk. Gold (`#a0792c`) is only for a handoff that has already happened and for the approval card once an agent asks.

## Campus photographs

Three photographs sit under the masthead, in this order:

- Harkness Tower, photographed by Ad Meskens (Wikimedia Commons, CC BY-SA 3.0).
- Evans Hall at the School of Management, photographed by Nick Allen (Wikimedia Commons, CC BY-SA 3.0).
- The Pierson College gate, photographed by Emilie Foyer (Wikimedia Commons, CC BY-SA 3.0).

## Handsome Dan

Two portraits of the mascot frame the title. On the left is the original Handsome Dan, a Pach Brothers photograph from about 1889 (public domain). On the right is Handsome Dan XIX, Kingman, on Cross Campus in March 2022, photographed by Joeshmonobody (Wikimedia Commons, CC BY-SA 4.0). The checking balance sits in the blue block beside Kingman so the number is the first thing you can check after a payment.

## Splinter and the turtles

The five agents are original drawings, not studio stills. Splinter, the rat in the robe with the staff, is the boss and stands alone at the top. The four turtles stand in a row beneath him, each joined to Splinter by a line:

- Leonardo, blue mask, is inventory.
- Donatello, purple mask, is accounting.
- Raphael, red mask, is facilities.
- Michelangelo, orange mask, is customer service.

The drawing is inline, so the chain can light up while a ticket runs. The turtle who is speaking gets a Yale blue ring. A turtle who has already spoken gets a gold ring. A line that has already been used turns gold, and the line for the latest handoff turns blue. Under the diagram, the thought chain lists each audit step in order: who was called, what they thought, what they said, and which tools they used. When the run finishes, the ticket is marked resolved and each agent who spoke gets a short summary.

## Money

Checking is the balance from `GET /api/cash`. Approving a prepared payment or purchase posts to `POST /api/approve`. The balance on the masthead updates from that response, and the number shifts gold for a moment when it falls.
