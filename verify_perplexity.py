try:
    import perplexityai
    print(f"Package found: {perplexityai}")
    print(f"Dir: {dir(perplexityai)}")
    try:
        from perplexityai import Perplexity
        print("Import 'from perplexityai import Perplexity' successful")
    except ImportError:
        print("Import 'from perplexityai import Perplexity' FAILED")
except ImportError:
    print("Package 'perplexityai' NOT FOUND")
