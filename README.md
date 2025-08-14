# AI Negotiation Simulator

This project simulates a negotiation scenario between a **Buyer AI agent** and a **Seller AI agent** using a language model. It allows testing different negotiation strategies over multiple rounds for various products, tracking deal outcomes, savings, and below-market percentages.


## Installation

Install the required Python packages:

```bash
pip install langchain langchain-community
```

--- 

## Explanation of Installations

- **langchain**: Provides an interface to integrate and use large language models for structured conversational agents.  
- **langchain-community**: Contains community-contributed chat models, including `ChatOllama`, which is used to generate dynamic negotiation responses.  
- **dataclasses, abc, enum, typing**: Standard Python modules used for structured data management, abstract base classes, enumerations, and type hinting.  
- **warnings**: Used to suppress deprecation warnings for cleaner runtime output.  

---

## Overview

This project simulates a negotiation between a **Buyer AI agent** and a **Seller AI agent** over multiple rounds. The negotiation is dynamic:

- Products have attributes like quantity, quality, origin, base market price, and other specifications.  
- Buyer agent uses a cautious, incremental offer strategy.  
- Seller agent starts with a premium price and negotiates strategically.  
- The simulation tracks deal status, rounds, savings, and below-market percentages.  

---

## Buyer and Seller Strategies

### Buyer Strategy
The Buyer AI agent is **cautious and diplomatic**. It maximizes savings by making small incremental offers and staying within budget limits. The buyer evaluates the seller’s offers carefully and responds politely, often using catchphrases like *“Let me think about that…”* or *“That’s pushing my budget.”* Depending on the deal status, the buyer either accepts a favorable offer, negotiates slightly higher, or expresses urgency if time is limited. The focus is on minimizing financial risk while still attempting to close the deal.  

### Seller Strategy
The Seller AI agent is **data-driven and strategic**. It aims to maximize profit while maintaining a positive relationship with the buyer. The seller starts with a premium price and responds to offers with calculated concessions, considering its internal minimum price. Catchphrases like *“I can offer you a fair deal”* or *“This price reflects the quality”* reinforce the product’s perceived value. The seller adapts its strategy over rounds, either closing quickly if profitable or signaling urgency to encourage the buyer to agree.  

---

## Mathematical Strategy

### Buyer Mathematical Strategy
The buyer calculates offers based on a fraction of the product’s base market price:

\[
\text{Initial Offer} = \min(\text{Base Market Price} \times 0.6, \text{Buyer Budget})
\]

During negotiation, the buyer increases its previous offer by up to 10% if the seller’s price is slightly higher:

\[
\text{Next Offer} = \min(\text{Last Offer} \times 1.1, \text{Buyer Budget})
\]

This cautious progression ensures savings while staying within budget limits.  

### Seller Mathematical Strategy
The seller starts with a markup on the base market price:

\[
\text{Opening Price} = \text{Base Market Price} \times 1.5
\]

During negotiation, the seller evaluates the buyer’s offer against its minimum acceptable price. If profitable, it accepts; otherwise, it calculates a counteroffer using:

\[
\text{Counteroffer} = \max(\text{Min Price}, \text{Buyer Offer} \times 1.05 \text{ to } 1.15)
\]

This ensures the seller maintains profitability while making strategic concessions.
