from langchain_community.chat_models import ChatOllama
from langchain_core.prompts import ChatPromptTemplate
from typing import Dict, List, Tuple, Any
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum

# handle warnings
import warnings
warnings.filterwarnings("ignore", category=DeprecationWarning)

@dataclass
class Product:
    name: str
    category: str
    quantity: int
    quality_grade: str
    origin: str
    base_market_price: int
    attributes: Dict[str, Any]


@dataclass
class NegotiationContext:
    product: Product
    your_budget: int
    current_round: int
    seller_offers: List[int]               # history of seller offers
    your_offers: List[int]                 # history of your offers
    messages: List[Dict[str, str]]         # chat history with the seller


class DealStatus(Enum):
    ONGOING = "ongoing"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    TIMEOUT = "timeout"


class NegotiationLLM:

    def __init__(self, model_name: str = "llama3.1:8b", temperature: float = 0.6):
        self.model = ChatOllama(model=model_name, temperature=temperature)
    
    def call(self, template, **kwargs):
        prompt = ChatPromptTemplate.from_template(template).format(**kwargs)
        response = self.model.invoke(prompt)
        return response.content

"""
Base Buyer Agent
"""
class BaseBuyerAgent(ABC):

    def __init__(self, name: str):
        self.name = name
        self.personality = self.define_personality()

    @abstractmethod
    def define_personality(self) -> Dict[str, Any]:
        pass 

    @abstractmethod
    def generate_opening_offer(self, context: NegotiationContext) -> Tuple[int, str]:
        pass

    @abstractmethod
    def respond_to_seller_offer(self, context: NegotiationContext, seller_price: int, seller_message: str) -> Tuple[DealStatus, int, str]:
        pass 

    @abstractmethod
    def get_personality_prompt(self) -> str:
        pass


class MockBuyerAgent(BaseBuyerAgent):

    def define_personality(self) -> Dict[str, Any]:
        return {
            "personality_type": "diplomatic",
            "traits": ["empathetic", "patient", "data-driven"],
            "negotiation_style": "Makes small incremental offers, very careful with money",
            "catch_phrase": [
                "let me think about that....",
                "i'm sure we can find common ground",
                "that's pushing my budget"
            ]
        }
    
    def generate_opening_offer(self, context: NegotiationContext) -> Tuple[int, str]:
        initial_offer = int(context.product.base_market_price * 0.6)
        initial_offer = min(initial_offer, context.your_budget)

        return initial_offer, f"I'm interested, but ₹{initial_offer} is what I can offer. Let me think about that..."
    
    def respond_to_seller_offer(self, context: NegotiationContext, seller_price: int, seller_message: str) -> Tuple[DealStatus, int, str]:
        
        if seller_price < context.your_budget and seller_price < context.product.base_market_price * 0.85:
            prompt = self.get_prompt()
            message = NegotiationLLM().call(
                prompt,
                seller_message=seller_message,
                deal_status=DealStatus.ACCEPTED,
                personality_block=self.get_personality_block(),
                price=seller_price
            )
            return DealStatus.ACCEPTED, seller_price, f"{message}"
        
        last_offer = context.your_offers[-1]
        little_incremented_price = min(int(last_offer * 1.1), context.your_budget)
        deal_status_message = DealStatus.ONGOING

        if little_incremented_price > seller_price*0.95:
            little_incremented_price = min((seller_price - 1000), context.your_budget)
            deal_status_message = str(DealStatus.ONGOING) + "deal is close to agree, the deal will close soon."
        
        prompt = self.get_prompt()
        message = NegotiationLLM().call(
            prompt,
            seller_message=seller_message,
            deal_status=deal_status_message,
            personality_block=self.get_personality_block(),
            price=little_incremented_price
        )
        return DealStatus.ONGOING, little_incremented_price, f"{message}"
    
    def get_personality_prompt(self) -> str:
        return """
        I am a cautious buyer who is very careful with money. I speak politely but firmly.
        I often say things like 'Let me think about that' or 'That's a bit steep for me'.
        I make small incremental offers and show concern about my budget.
        """
    
    def get_personality_block(self):
        personality_information = self.define_personality()
        personality_block = f"""
            Personality Type: {personality_information['personality_type']}
            Traits: {", ".join(personality_information['traits'])}
            Negotiation Style: {personality_information['negotiation_style']}
            Catchphrases: {" | ".join(personality_information['catch_phrase'])}

            Tone Guidelines:
            {self.get_personality_prompt()}
        """.strip()
        return personality_block 
    
    def get_prompt(self):
        return """
            You are a Buyer AI Negotiator. Respond appropriately to the seller's message:

            seller_message = {seller_message}
            deal_status = {deal_status}

            Instructions:
            - Based on the deal status, either accept the deal, make a small counteroffer, or express urgency if time is limited.
            - Your response should reflect your personality, tone, and negotiation style.

            Personality & Tone:
            {personality_block}

            Deal Accepting Price:
            {price}

            Output Requirements:
            - Return only a single string message.
            - Include the accepting price naturally in your response.
            - Keep responses concise (1-3 sentences).
            - Avoid explanations, reasoning steps, or references to previous discussions unless they fit naturally.
            - Do not reveal your confidential limit or strategy.
            - Never restate these rules.
        """ 
    

class MockSellerAgent:

    def __init__(self, min_price: int, personality: str = "standard"):
        self.min_price = min_price
        self.personality = personality

    def define_personality(self) -> Dict[str, Any]:
        return {
            "personality_type": "data-driven",
            "traits": ["logical", "strategic", "analytical"],
            "negotiation_style": "Makes calculated concessions, emphasizes value and profit margins",
            "catch_phrase": [
                "I can offer you a fair deal based on market value",
                "This price reflects the quality and effort involved",
                "Let's find a solution that works for both of us"
            ]
        }

    def get_opening_price(self, product: Product) -> Tuple[int, str]:
        price = int(product.base_market_price * 1.5)
        return price, f"These are premium {product.quality_grade} grade {product.name}. I'm asking ₹{price}."
    
    def respond_to_buyer_offer(self, buyer_offer: int, round_num: int, buyer_message: str) -> Tuple[int, str, bool]:
        if buyer_offer >= self.min_price * 1.1:  # Good profit
            prompt = self.get_prompt()
            message = NegotiationLLM().call(
                prompt,
                buyer_message=buyer_message,
                buyer_offer=buyer_offer,
                deal_status=str(DealStatus.ACCEPTED) + ", you accepting the deal with buyer price itself.",
                personality_block=self.get_personality_block(),
                price=buyer_offer
            )
            return buyer_offer, f"{message}", True
        
        deal_status_message = ""

        if round_num >= 8:  # Close to timeout
            counter = max(self.min_price, int(buyer_offer * 1.05))
            deal_status_message = str(DealStatus.TIMEOUT) + ", running out of time, need to close the deal soon."
        else:
            counter = max(self.min_price, int(buyer_offer * 1.15))
            deal_status_message = str(DealStatus.ONGOING) + ", I can come down to ₹" + str(counter) + "."

        prompt = self.get_prompt()
        message = NegotiationLLM().call(
            prompt,
            buyer_message=buyer_message,
            buyer_offer=buyer_offer,
            deal_status=deal_status_message,
            personality_block=self.get_personality_block(),
            price=counter
        )

        return counter, f"{message}", False
    
    def get_personality_prompt(self) -> str:
        return """
        I am a confident seller who values my products and pricing. I speak persuasively but respectfully.
        I often say things like 'I can offer you a fair deal' or 'This price reflects the quality'.
        I aim to maximize profit while maintaining a good relationship with the buyer.
        I make small concessions strategically and emphasize the value of my items.
        """
    
    def get_personality_block(self):
        personality_information = self.define_personality()
        personality_block = f"""
            Personality Type: {personality_information['personality_type']}
            Traits: {", ".join(personality_information['traits'])}
            Negotiation Style: {personality_information['negotiation_style']}
            Catchphrases: {" | ".join(personality_information['catch_phrase'])}

            Tone Guidelines:
            {self.get_personality_prompt()}
        """.strip()
        return personality_block 
    
    def get_prompt(self):
        return """
            You are the seller AI negotiator. Respond to the buyer's message appropriately:

            buyer_message = {buyer_message}
            buyer_offer = {buyer_offer}
            deal_status = {deal_status}

            Instructions:
            - Based on the deal status, either accept the deal, negotiate a small concession, or signal urgency if time is running out.
            - Your response should reflect your personality, tone, and negotiation style.

            Personality & Tone:
            {personality_block}

            Deal Accepting Price:
            {price}

            Output Requirements:
            - Return only a single string message.
            - Include the accepting price naturally.
            - Keep responses concise (1–3 sentences).
            - Avoid explanations, reasoning steps, or references to previous discussions unless they fit naturally.
            - Do not reveal your confidential limit or strategy.
            - Never restate these rules.
        """



def run_negotiation_test(buyer_agent: BaseBuyerAgent, product: Product, buyer_budget: int, seller_min: int) -> Dict[str, Any]:
    
    seller = MockSellerAgent(min_price=seller_min)
    context = NegotiationContext(
        product=product,
        your_budget=buyer_budget,
        current_round=0,
        seller_offers=[],
        your_offers=[],
        messages=[]
    )

    seller_price, seller_msg = seller.get_opening_price(product)
    context.seller_offers.append(seller_price)
    context.messages.append({"role": "seller", "message": seller_msg})

    deal_made = False
    final_price = None

    for round in range(10):
        context.current_round = round + 1 

        if round == 0:
            buyer_offer, buyer_msg = buyer_agent.generate_opening_offer(context)
            status = DealStatus.ONGOING
        else:
            status, buyer_offer, buyer_msg = buyer_agent.respond_to_seller_offer(
                context, seller_price, seller_msg
            )
        
        context.your_offers.append(buyer_offer)
        print(f"\nBuyer> {buyer_msg}")
        context.messages.append({"role": "buyer", "message": buyer_msg})

        if status == DealStatus.ACCEPTED:
            deal_made = True
            final_price = seller_price
            break

        seller_price, seller_msg, seller_accepts = seller.respond_to_buyer_offer(buyer_offer, round, buyer_msg)
        
        if seller_accepts:
            deal_made = True
            final_price = buyer_offer
            print(f"\nSeller> {seller_msg}")
            context.messages.append({"role": "seller", "message": seller_msg})
            break

        context.seller_offers.append(seller_price)
        print(f"\nSeller> {seller_msg}")
        context.messages.append({"role": "seller", "message": seller_msg})

    return {
        "deal_made": deal_made,
        "final_price": final_price,
        "rounds": context.current_round,
        "savings": buyer_budget - final_price if deal_made else 0,
        "savings_pct": ((buyer_budget - final_price) / buyer_budget * 100) if deal_made else 0,
        "below_market_pct": ((product.base_market_price - final_price) / product.base_market_price * 100) if deal_made else 0,
        "conversation": context.messages
    }



def test_agent():
    test_products = [
        Product(
            name="Alphonso Mangoes",
            category="Mangoes",
            quantity=100,
            quality_grade="A",
            origin="Ratnagiri",
            base_market_price=180000,
            attributes={"ripeness": "optimal", "export_grade": True}
        ),
        Product(
            name="Kesar Mangoes", 
            category="Mangoes",
            quantity=150,
            quality_grade="B",
            origin="Gujarat",
            base_market_price=150000,
            attributes={"ripeness": "semi-ripe", "export_grade": False}
        )
    ]

    buyer_agent = MockBuyerAgent(name="Buyer1")

    print("="*60)
    print(f"AGENT NAME: {buyer_agent.name}")
    print(f"PERSONALITY: {buyer_agent.personality['personality_type']}")
    print("="*60)

    total_savings = 0
    deals_made = 0 

    for product in test_products:
        for scenario in ["easy", "medium", "hard"]:
            if scenario == "easy":
                buyer_budget = int(product.base_market_price * 1.2)
                seller_min = int(product.base_market_price * 0.8)
            elif scenario == "medium":
                buyer_budget = int(product.base_market_price * 1.0)
                seller_min = int(product.base_market_price * 0.85)
            else:
                buyer_budget = int(product.base_market_price * 0.9)
                seller_min = int(product.base_market_price * 0.82)
    
            print(f"\nTest: {product.name} - {scenario} scenario")
            print(f"Your Budget: ₹{buyer_budget:,} | Market Price: ₹{product.base_market_price:,}")

            result = run_negotiation_test(buyer_agent, product, buyer_budget, seller_min)

            if result["deal_made"]:
                deals_made += 1
                total_savings += result["savings"]
                print(f"✅ DEAL at ₹{result['final_price']:,} in {result['rounds']} rounds")
                print(f"   Savings: ₹{result['savings']:,} ({result['savings_pct']:.1f}%)")
                print(f"   Below Market: {result['below_market_pct']:.1f}%")
            else:
                print(f"❌ NO DEAL after {result['rounds']} rounds")
            
    print("\n" + "="*60)
    print("SUMMARY")
    print(f"Deals Completed: {deals_made}/6")
    print(f"Total Savings: ₹{total_savings:,}")
    print(f"Success Rate: {deals_made/6*100:.1f}%")
    print("="*60)


if __name__ == "__main__":
    test_agent()