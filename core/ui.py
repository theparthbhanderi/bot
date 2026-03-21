import html
from telegram import InlineKeyboardButton, InlineKeyboardMarkup

# 🧱 CONFIG-BASED BUTTON SYSTEM
BUTTON_LAYOUT = [
    [("🤖 AI Chat", "ai"), ("🤖 Agent Mode", "agent")],
    [("🧠 Research", "research"), ("📰 News", "news")],
    [("🎬 YouTube", "youtube"), ("🔍 Fact Check", "fact")],
    [("🖼️ OCR / PDF", "ocr"), ("🎨 Image Gen", "image")],
    [("💻 Coding", "coding"), ("📚 Knowledge Hub", "kb")],
    [("👨‍💻 Developer", "dev")]
]

# 💎 PREMIUM TOUCHES
DIVIDER = "━━━━━━━━━━━━━━━"
FOOTER_BRANDING = "🚀 Powered by Parth"

def build_main_menu() -> InlineKeyboardMarkup:
    """Dynamically generate InlineKeyboardMarkup. No hardcoded buttons."""
    keyboard = []
    for row in BUTTON_LAYOUT:
        keyboard_row = [
            InlineKeyboardButton(text, callback_data=f"btn_{data}") 
            for text, data in row
        ]
        keyboard.append(keyboard_row)
        
    return InlineKeyboardMarkup(keyboard)

def create_card(title: str, content: str, tip: str = None) -> str:
    """Premium Card Layout Template."""
    card = f"🧠 <b>{html.escape(title)}</b>\n\n{content}\n\n"
    if tip:
        card += f"💡 {html.escape(tip)}\n\n"
    card += f"{DIVIDER}\n{FOOTER_BRANDING}"
    return card

def format_smart_response(title: str, short_answer: str, details: list, tip: str = None) -> str:
    """
    Format standard response using the clean structured template.
    """
    lines = [
        f"🧠 <b>{html.escape(title)}</b>\n",
        "⚡ <b>Quick Answer</b>",
        html.escape(short_answer),
        "\n📖 <b>Details</b>"
    ]
    
    # Render detail points
    for point in details:
        lines.append(f"• {html.escape(point)}")
        
    if tip:
        lines.append(f"\n💡 <b>Tip</b>\n{html.escape(tip)}")
        
    lines.append(f"\n{DIVIDER}")
    lines.append(FOOTER_BRANDING)
    
    return "\n".join(lines)

def build_smart_actions(simplify: bool = True, translate: bool = True, back: bool = True) -> InlineKeyboardMarkup:
    """Smart response buttons appended to formatted outputs."""
    buttons = []
    if simplify:
        buttons.append(InlineKeyboardButton("Simplify", callback_data="action_simplify"))
    if translate:
        buttons.append(InlineKeyboardButton("Translate", callback_data="action_translate"))
        
    layout = [buttons]
    if back:
        layout.append([InlineKeyboardButton("Back", callback_data="btn_main")])
        
    return InlineKeyboardMarkup(layout)
