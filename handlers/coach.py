"""
Personal AI Coach Handler for KINGPARTH Bot
Handles goal setting, daily tasks, and progress tracking.
"""

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from services.utils import format_premium_response, FOOTER, get_translation_keyboard
from services.llm_service import async_chat_completion
from database import db
import json
import logging

logger = logging.getLogger(__name__)

async def coach_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Main menu for Personal AI Coach."""
    user_id = update.effective_user.id
    active_goal = db.get_active_goal(user_id)

    if not active_goal:
        text = format_premium_response(
            title="Personal AI Coach",
            short="Welcome to your personal growth journey!",
            points=[
                "Set long-term goals (IELTS, Coding, Fitness)",
                "Get AI-generated daily study plans",
                "Track your progress automatically"
            ],
            tip="Use /setgoal [your goal] to start!"
        )
        keyboard = [[InlineKeyboardButton("🎯 Set My First Goal", callback_data="coach_set_goal")]]
    else:
        progress = db.get_coach_progress(user_id, active_goal['id'])
        text = format_premium_response(
            title=f"Coach: {active_goal['goal_title']}",
            short=f"You are doing great! Current progress: {progress['percentage']:.1f}%",
            points=[
                f"🎯 Goal: {active_goal['goal_title']}",
                f"✅ Completed: {progress['completed']}/{progress['total']} tasks",
                "📅 Daily tasks are ready for you!"
            ],
            tip="Use /tasks to see what's due today."
        )
        keyboard = [
            [InlineKeyboardButton("📝 Today's Tasks", callback_data="coach_tasks")],
            [InlineKeyboardButton("📊 Detailed Progress", callback_data="coach_progress")],
            [InlineKeyboardButton("🔄 Update Goal", callback_data="coach_set_goal")]
        ]

    reply_markup = InlineKeyboardMarkup(keyboard)
    if update.message:
        await update.message.reply_text(text, parse_mode="HTML", reply_markup=reply_markup)
    else:
        await update.callback_query.edit_message_text(text, parse_mode="HTML", reply_markup=reply_markup)

async def set_goal_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /setgoal command."""
    user_id = update.effective_user.id
    if not context.args:
        text = format_premium_response(
            title="Set Your Goal",
            short="Tell me what you want to achieve.",
            points=[
                "Example: /setgoal IELTS preparation in 3 months",
                "Example: /setgoal Learn Python for Data Science",
                "Example: /setgoal 30-day fitness challenge"
            ]
        )
        await update.message.reply_text(text, parse_mode="HTML")
        return

    goal_text = " ".join(context.args)
    await update.message.reply_text("🧠 <b>AI Coach is crafting your personalized plan...</b>", parse_mode="HTML")

    # Generate plan using AI
    prompt = f"""You are a professional Personal AI Coach. 
    User Goal: {goal_text}
    Create a structured 7-day initial plan.
    Return ONLY a JSON object:
    {{
        "title": "Short Goal Title",
        "description": "Brief professional summary",
        "tasks": ["Task 1 for Day 1", "Task 2 for Day 1", "Task 3 for Day 1"]
    }}
    Ensure tasks are actionable and high-value."""

    try:
        response = await async_chat_completion([{"role": "user", "content": prompt}], max_tokens=1000)
        plan_data = json.loads(response.strip().replace('```json', '').replace('```', ''))
        
        # Save to DB
        goal_id = db.create_coach_goal(user_id, plan_data['title'], plan_data['description'], response)
        
        # Add tasks for Day 1
        for task_title in plan_data['tasks']:
            db.add_coach_task(goal_id, user_id, task_title)

        success_text = format_premium_response(
            title="Goal Set Successfully! 🚀",
            short=plan_data['description'],
            points=[f"Target: {plan_data['title']}"] + [f"• {t}" for p, t in enumerate(plan_data['tasks'])],
            tip="Check your daily tasks with /tasks"
        )
        context.user_data["last_response"] = success_text
        
        keyboard = get_translation_keyboard().inline_keyboard
        await update.message.reply_text(success_text, parse_mode="HTML", reply_markup=InlineKeyboardMarkup(keyboard))

    except Exception as e:
        logger.error(f"Error in set_goal: {e}")
        await update.message.reply_text("⚠️ <b>Failed to generate plan. Please try again.</b>", parse_mode="HTML")

async def tasks_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /tasks command."""
    user_id = update.effective_user.id
    tasks = db.get_daily_tasks(user_id)

    if not tasks:
        text = format_premium_response(
            title="No Pending Tasks",
            short="You've completed all tasks for today or haven't set a goal yet!",
            tip="Use /coach to manage your journey."
        )
        await update.message.reply_text(text, parse_mode="HTML")
        return

    points = []
    keyboard = []
    for i, task in enumerate(tasks):
        points.append(f"{i+1}. {task['task_title']}")
        keyboard.append([InlineKeyboardButton(f"✅ Mark Task {i+1} Done", callback_data=f"coach_done_{task['id']}")])

    text = format_premium_response(
        title="Today's Tasks",
        short="Focus on these to reach your goal.",
        points=points
    )
    
    await update.message.reply_text(text, parse_mode="HTML", reply_markup=InlineKeyboardMarkup(keyboard))

async def complete_task_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Callback for marking tasks as completed."""
    query = update.callback_query
    task_id = int(query.data.split('_')[2])
    
    db.complete_task(task_id)
    await query.answer("Task marked as completed! 🎉")
    
    # Refresh task list
    await tasks_handler(update, context)
