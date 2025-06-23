import os
from openai import OpenAI
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class OpenAIService:
    """Service for interacting with OpenAI API"""
    
    def __init__(self):
        self.api_key = os.getenv("OPENAI_API_KEY")
        self.client = OpenAI(api_key=self.api_key)
        self.model = "gpt-3.5-turbo"  # Can also use "gpt-4o-mini" if available
        
    async def summarize_article(self, article):
        """
        Summarize a news article using OpenAI's ChatCompletion API
        
        Args:
            article (dict): Article containing title, description, and content
            
        Returns:
            str: Summarized article text
        """
        try:
            # Prepare article text for summarization
            article_text = f"Title: {article.get('title', '')}\n"
            article_text += f"Description: {article.get('description', '')}\n"
            
            # Add content if available and not too long
            content = article.get('content', '')
            if content and len(content) < 4000:
                article_text += f"Content: {content}\n"
            
            # Create the prompt
            prompt = f"Summarize the following news article in 2-3 concise sentences. Do not use any introductory phrases like 'Hey there', 'Did you know', or greetings. Do not repeat the title or start with phrases like 'Title:' or 'This article:'. Start directly with the summary content: {article_text}"
            
            # Call OpenAI API
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a helpful assistant that summarizes news articles in a clear, direct manner without using introductory phrases, greetings, or meta-references to the article itself. Provide only the essential information."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=150,
                temperature=0.7
            )
            
            # Extract and return the summary
            summary = response.choices[0].message.content.strip()
            return summary
            
        except Exception as e:
            return f"Error generating summary: {str(e)}"
