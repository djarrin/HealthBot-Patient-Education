#!/usr/bin/env python3
"""
Generate and save the HealthBot workflow graph image.
Simple script that creates the graph and saves the Mermaid PNG to a file.
"""

import os
import sys

# Add the src directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

# Set up environment variables for local testing
os.environ.setdefault('OPENAI_API_KEY', 'test-key')
os.environ.setdefault('TAVILY_API_KEY', 'test-key')
os.environ.setdefault('OPENAI_BASE_URL', 'https://api.openai.com/v1')
os.environ.setdefault('AWS_REGION', 'us-east-1')
os.environ.setdefault('SESSION_STATE_TABLE', 'healthbot-test-table')


def generate_graph_image():
    """Generate and save the graph image"""
    print("🏥 Generating HealthBot Workflow Graph Image")
    print("=" * 50)
    
    try:
        # Import the production build_graph function and MemorySaver
        from handlers.healthbot_graph import build_graph
        from langgraph.checkpoint.memory import MemorySaver
        
        print("🔍 Building production graph...")
        
        # Create a MemorySaver for local testing
        checkpointer = MemorySaver()
        
        # Use the real build_graph function with our local checkpointer
        graph = build_graph(checkpointer=checkpointer)
        
        print("✅ Production graph built successfully!")
        
        # Get the graph object
        graph_obj = graph.get_graph()
        
        print("🖼️  Generating Mermaid PNG...")
        
        # Generate the Mermaid PNG (like in the notebook)
        graph_image = graph_obj.draw_mermaid_png()
        
        # Save the image to a file
        output_path = "healthbot_workflow_graph.png"
        with open(output_path, "wb") as f:
            f.write(graph_image)
        
        print(f"✅ Graph image saved to: {output_path}")
        print(f"📁 Full path: {os.path.abspath(output_path)}")
        
        return output_path
        
    except Exception as e:
        print(f"❌ Error generating graph image: {e}")
        import traceback
        traceback.print_exc()
        return None


def main():
    """Main function"""
    output_path = generate_graph_image()
    
    if output_path:
        print(f"\n🎉 Success! Your graph image is saved at:")
        print(f"   {os.path.abspath(output_path)}")
        print(f"\n💡 You can now open this PNG file to see your HealthBot workflow graph!")
    else:
        print("❌ Failed to generate graph image")


if __name__ == "__main__":
    main()
