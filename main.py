import asyncio
import sys
from tqdm import tqdm
from engine.research_engine import ResearchEngine
import time

async def async_main():
    print("="*50)
    print("   Modular Academic Research Engine (MARE)")
    print("   [ASYNC MULTI-AGENT MODE]")
    print("="*50)
    
    engine = ResearchEngine()
    
    print("\nSelect Mode:")
    print("1. General Keyword (Boolean Expansion)")
    print("2. Detailed Description (Relevance Profiling)")
    
    try:
        mode_input = input("\nEnter choice (1/2): ")
        if not mode_input: return
        mode = int(mode_input)
        if mode not in [1, 2]:
            print("Invalid choice. Exiting.")
            return
    except ValueError:
        print("Invalid input. Exiting.")
        return

    user_input = input("\nEnter your search keywords or problem description:\n> ")
    if not user_input: return
    
    print("\nStarting Parallel Research Pipeline...\n")
    
    # Initialize progress bars
    outer_bar = tqdm(total=0, desc="Initializing", position=0, leave=True)
    inner_bar = tqdm(total=0, desc="Idle", position=1, leave=False)
    
    # Connect engine to progress bars
    engine.set_progress_callbacks(outer_callback=outer_bar, inner_callback=inner_bar)
    
    try:
        start_time = time.time()
        report = await engine.run_pipeline(mode, user_input)
        
        outer_bar.close()
        inner_bar.close()
        
        if report.startswith("Error:"):
            print(f"\n{report}")
        else:
            print("\n" + "="*50)
            print(f" RESEARCH SYNTHESIS REPORT (Time taken: {time.time() - start_time:.2f}s)")
            print("="*50 + "\n")
            print(report)
            
            with open("research_report.md", "w", encoding="utf-8") as f:
                f.write(report)
            print("\nReport saved to research_report.md")
            
    except Exception as e:
        print(f"\nAn error occurred during the pipeline: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await engine.shutdown()
        outer_bar.close()
        inner_bar.close()

if __name__ == "__main__":
    asyncio.run(async_main())
