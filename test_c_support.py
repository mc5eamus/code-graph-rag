#!/usr/bin/env python3
"""Test script to verify C language support in the code-graph-rag system."""

from codebase_rag.parser_loader import load_parsers
from codebase_rag.language_config import get_language_config_by_name

# Test C code sample
c_code = """
#include <stdio.h>
#include <stdlib.h>

struct Point {
    int x, y;
};

union Data {
    int i;
    float f;
};

enum Color {
    RED, GREEN, BLUE
};

int add(int a, int b) {
    return a + b;
}

void print_point(struct Point *p) {
    printf("Point: (%d, %d)\\n", p->x, p->y);
}

int main() {
    struct Point p = {10, 20};
    int result = add(5, 3);
    print_point(&p);
    printf("Result: %d\\n", result);
    return 0;
}
"""

def test_c_support():
    """Test C language parsing capabilities."""
    print("Testing C language support...")
    
    # Load parsers
    try:
        parsers, queries = load_parsers()
        print(f"✓ Parsers loaded successfully")
        print(f"  Available languages: {list(parsers.keys())}")
    except Exception as e:
        print(f"✗ Failed to load parsers: {e}")
        return False
    
    # Check if C is available
    if 'c' not in parsers:
        print("✗ C parser not found in available parsers")
        return False
    print("✓ C parser is available")
    
    # Get C language configuration
    c_config = get_language_config_by_name('c')
    if not c_config:
        print("✗ C language configuration not found")
        return False
    print("✓ C language configuration loaded")
    print(f"  File extensions: {c_config.file_extensions}")
    print(f"  Function node types: {c_config.function_node_types}")
    print(f"  Class node types: {c_config.class_node_types}")
    
    # Test parsing C code
    try:
        parser = parsers['c']
        tree = parser.parse(c_code.encode('utf-8'))
        print("✓ C code parsed successfully")
        
        # Test function query
        function_query = queries['c']['functions']
        if function_query:
            matches = function_query.matches(tree.root_node)
            functions = []
            for match in matches:
                for node, capture_name in match:
                    if capture_name == 'function':
                        functions.append(node.text.decode('utf-8'))
            print(f"✓ Functions found: {len(functions)}")
            for func in functions:
                print(f"  - {func}")
        
        # Test class query (structs/unions/enums in C)
        class_query = queries['c']['classes']
        if class_query:
            matches = class_query.matches(tree.root_node)
            classes = []
            for match in matches:
                for node, capture_name in match:
                    if capture_name == 'class':
                        classes.append(node.text.decode('utf-8'))
            print(f"✓ Types found: {len(classes)}")
            for cls in classes:
                print(f"  - {cls}")
        
        # Test call query
        call_query = queries['c']['calls']
        if call_query:
            matches = call_query.matches(tree.root_node)
            calls = []
            for match in matches:
                for node, capture_name in match:
                    if capture_name == 'call':
                        calls.append(node.text.decode('utf-8'))
            print(f"✓ Calls found: {len(calls)}")
            for call in calls[:5]:  # Show first 5 calls
                print(f"  - {call}")
        
    except Exception as e:
        print(f"✗ Failed to parse C code: {e}")
        return False
    
    print("\n🎉 C language support is working correctly!")
    return True

if __name__ == "__main__":
    test_c_support()