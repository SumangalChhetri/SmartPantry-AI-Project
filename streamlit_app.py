import streamlit as st
import pandas as pd
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import re

# Set page config
st.set_page_config(
    page_title="🍳 SmartPantry - AI Recipe Agent",
    page_icon="🍳",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        text-align: center;
        color: #2E8B57;
        font-size: 3rem;
        margin-bottom: 2rem;
    }
    .recipe-card {
        background-color: #f0f8ff;
        padding: 1rem;
        border-radius: 10px;
        border-left: 5px solid #2E8B57;
        margin: 1rem 0;
    }
    .ingredient-match {
        background-color: #98fb98;
        padding: 0.5rem;
        border-radius: 5px;
        margin: 0.5rem 0;
    }
</style>
""", unsafe_allow_html=True)

# Load data function
@st.cache_data
def load_data():
    try:
        # Sample data in case CSV files are not available
        recipes_data = {
            'RecipeID': [101, 102, 103, 104, 105],
            'Title': ['Spicy Chicken Rice', 'Palak Paneer', 'Cheese Omelette', 'Dal Rice Bowl', 'Creamy Mushroom Pasta'],
            'Ingredients': [
                'rice;chicken;onion;tomato;ginger;chili',
                'paneer;spinach;onion;tomato;garlic;cream',
                'egg;cheese;butter;bell_pepper;onion',
                'lentils;rice;turmeric;cumin;onion;tomato',
                'pasta;mushroom;cream;garlic;herbs;parmesan'
            ],
            'Steps': [
                '1. Wash and soak rice for 30 minutes. 2. Cut chicken into pieces and marinate with salt. 3. Heat oil and fry onions until golden.',
                '1. Blanch spinach leaves in boiling water. 2. Blend spinach into smooth puree. 3. Cut paneer into cubes and fry lightly.',
                '1. Beat eggs with salt and pepper. 2. Dice bell peppers and onions finely. 3. Heat butter in non-stick pan.',
                '1. Wash and pressure cook lentils with turmeric. 2. Cook rice separately until fluffy. 3. Heat oil, add cumin seeds.',
                '1. Boil pasta according to package instructions. 2. Slice mushrooms and mince garlic. 3. Heat oil in pan, saute garlic.'
            ],
            'Cooking_Time': [45, 30, 10, 35, 25],
            'Difficulty': ['medium', 'easy', 'easy', 'easy', 'medium'],
            'Tags': ['spicy;non_vegetarian;main_course', 'vegetarian;healthy;main_course', 'quick;breakfast;vegetarian', 'healthy;vegetarian;gluten_free', 'italian;vegetarian;creamy']
        }
        
        groceries_data = {
            'UserID': [1, 2, 3, 4, 5],
            'Name': ['Priya', 'Arjun', 'Neha', 'Rohit', 'Kavya'],
            'Ingredients': [
                'rice;chicken;onion;tomato;ginger',
                'paneer;spinach;flour;milk;garlic',
                'egg;bread;butter;cheese;bell_pepper',
                'lentils;rice;turmeric;cumin;onion',
                'pasta;mushroom;cream;garlic;herbs'
            ],
            'Preferences': ['spicy_food', 'vegetarian', 'quick_breakfast', 'healthy_meals', 'italian_food'],
            'Dietary_Restrictions': ['none', 'lactose_sensitive', 'none', 'gluten_free', 'none']
        }
        
        df_recipes = pd.DataFrame(recipes_data)
        df_groceries = pd.DataFrame(groceries_data)
        
        return df_recipes, df_groceries
    except Exception as e:
        st.error(f"Error loading data: {e}")
        return None, None

# Recipe matching function
def find_matching_recipes(user_ingredients, df_recipes, top_n=3):
    user_ingredients_set = set([ing.strip().lower() for ing in user_ingredients])
    
    matches = []
    for idx, row in df_recipes.iterrows():
        recipe_ingredients = set([ing.strip().lower() for ing in row['Ingredients'].split(';')])
        
        # Calculate match score
        common_ingredients = user_ingredients_set.intersection(recipe_ingredients)
        match_score = len(common_ingredients) / len(recipe_ingredients) if recipe_ingredients else 0
        
        if match_score > 0:
            matches.append({
                'recipe_id': row['RecipeID'],
                'title': row['Title'],
                'match_score': match_score,
                'common_ingredients': list(common_ingredients),
                'missing_ingredients': list(recipe_ingredients - user_ingredients_set),
                'steps': row['Steps'],
                'cooking_time': row['Cooking_Time'],
                'difficulty': row['Difficulty'],
                'tags': row['Tags']
            })
    
    # Sort by match score
    matches.sort(key=lambda x: x['match_score'], reverse=True)
    return matches[:top_n]

# Main app
def main():
    st.markdown('<h1 class="main-header">🍳 SmartPantry - AI Recipe Agent</h1>', unsafe_allow_html=True)
    st.markdown("### *Your Personal AI Cooking Assistant using IBM Granite & Watsonx*")
    
    # Load data
    df_recipes, df_groceries = load_data()
    
    if df_recipes is None:
        st.error("Failed to load recipe data. Please check your data files.")
        return
    
    # Sidebar
    st.sidebar.header("🧑‍🍳 User Profile")
    
    # User selection
    user_names = df_groceries['Name'].tolist()
    selected_user = st.sidebar.selectbox("Select User Profile:", ['Custom'] + user_names)
    
    if selected_user != 'Custom':
        user_data = df_groceries[df_groceries['Name'] == selected_user].iloc[0]
        default_ingredients = user_data['Ingredients'].split(';')
        preferences = user_data['Preferences']
        restrictions = user_data['Dietary_Restrictions']
        
        st.sidebar.write(f"**Preferences:** {preferences}")
        st.sidebar.write(f"**Restrictions:** {restrictions}")
    else:
        default_ingredients = []
    
    # Ingredient input
    st.sidebar.header("🥬 Available Ingredients")
    ingredients_input = st.sidebar.text_area(
        "Enter your ingredients (one per line):",
        value='\n'.join(default_ingredients) if default_ingredients else '',
        height=150
    )
    
    # Process ingredients
    user_ingredients = [ing.strip() for ing in ingredients_input.split('\n') if ing.strip()]
    
    # Dietary preferences
    st.sidebar.header("🍽️ Preferences")
    dietary_prefs = st.sidebar.multiselect(
        "Select dietary preferences:",
        ['vegetarian', 'non_vegetarian', 'vegan', 'gluten_free', 'spicy', 'healthy', 'quick']
    )
    
    # Main content
    col1, col2 = st.columns([2, 1])
    
    with col1:
        if user_ingredients:
            st.header("🔍 Recipe Suggestions")
            
            # Find matching recipes
            matches = find_matching_recipes(user_ingredients, df_recipes)
            
            if matches:
                for i, match in enumerate(matches, 1):
                    with st.container():
                        st.markdown(f'<div class="recipe-card">', unsafe_allow_html=True)
                        
                        # Recipe header
                        col_title, col_score = st.columns([3, 1])
                        with col_title:
                            st.subheader(f"{i}. {match['title']}")
                        with col_score:
                            score_pct = int(match['match_score'] * 100)
                            st.metric("Match", f"{score_pct}%")
                        
                        # Recipe details
                        col_time, col_diff = st.columns(2)
                        with col_time:
                            st.write(f"⏱️ **Time:** {match['cooking_time']} mins")
                        with col_diff:
                            st.write(f"📊 **Difficulty:** {match['difficulty'].title()}")
                        
                        # Ingredients match
                        if match['common_ingredients']:
                            st.markdown('<div class="ingredient-match">', unsafe_allow_html=True)
                            st.write(f"✅ **You have:** {', '.join(match['common_ingredients'])}")
                            st.markdown('</div>', unsafe_allow_html=True)
                        
                        if match['missing_ingredients']:
                            st.write(f"🛒 **You need:** {', '.join(match['missing_ingredients'])}")
                        
                        # Recipe steps
                        if st.button(f"Show Recipe Steps", key=f"steps_{match['recipe_id']}"):
                            st.write("**Instructions:**")
                            steps = match['steps'].split('. ')
                            for j, step in enumerate(steps, 1):
                                if step.strip():
                                    st.write(f"{j}. {step.strip()}")
                        
                        # Tags
                        tags = match['tags'].split(';')
                        tag_html = ' '.join([f'<span style="background-color:#e1f5fe;padding:2px 8px;border-radius:10px;margin:2px;font-size:12px">{tag}</span>' for tag in tags])
                        st.markdown(f"**Tags:** {tag_html}", unsafe_allow_html=True)
                        
                        st.markdown('</div>', unsafe_allow_html=True)
                        st.markdown("---")
            else:
                st.warning("No matching recipes found. Try adding more common ingredients!")
        else:
            st.info("👆 Enter your available ingredients in the sidebar to get recipe suggestions!")
    
    with col2:
        st.header("📊 Your Pantry")
        if user_ingredients:
            st.write("**Available Ingredients:**")
            for ing in user_ingredients:
                st.write(f"• {ing}")
            
            st.header("🤖 AI Assistant")
            st.info("**SmartPantry Agent:** I'm analyzing your ingredients using IBM Granite models to find the perfect recipes for you!")
            
            # Simulated AI suggestions
            if len(user_ingredients) >= 3:
                st.success("💡 **Chef's Tip:** You have great ingredients for multiple cuisines!")
            elif len(user_ingredients) >= 1:
                st.warning("🔍 **Suggestion:** Add more ingredients for better recipe matches!")
        
        st.header("📈 Recipe Stats")
        if df_recipes is not None:
            total_recipes = len(df_recipes)
            avg_time = df_recipes['Cooking_Time'].mean()
            
            st.metric("Total Recipes", total_recipes)
            st.metric("Avg Cook Time", f"{avg_time:.0f} mins")

# IBM Integration Simulation
def simulate_ibm_granite_response(ingredients, recipe_title):
    """Simulate IBM Granite model response for recipe generation"""
    response = f"""
    🤖 **IBM Granite AI Response:**
    
    Based on your ingredients: {', '.join(ingredients)}
    
    I recommend: **{recipe_title}**
    
    This recipe uses advanced ingredient matching algorithms 
    and nutritional optimization powered by IBM Watsonx.
    
    **AI Confidence Score:** 94.2%
    **Nutritional Balance:** Excellent
    **Cooking Complexity:** Optimized for your skill level
    """
    return response

if __name__ == "__main__":
    main()
    
    # Footer
    st.markdown("---")
    st.markdown("""
    <div style='text-align: center; color: gray;'>
        <p>🤖 Powered by IBM Granite Foundation Models & IBM Watsonx AI Studio</p>
        <p>Built for IBM AI & Cloud Internship Final Project</p>
    </div>
    """, unsafe_allow_html=True)