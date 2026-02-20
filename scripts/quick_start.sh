#!/bin/bash
# Quick start script for NOAH PostgreSQL to Neo4j Converter

set -e  # Exit on error

echo "🚀 NOAH PostgreSQL to Neo4j Converter - Quick Start"
echo "=" repeat 60

# Check if Python 3 is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3.10+ first."
    exit 1
fi

echo "✓ Python 3 found: $(python3 --version)"

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
    echo "✓ Virtual environment created"
else
    echo "✓ Virtual environment already exists"
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "📥 Installing dependencies..."
pip install --upgrade pip -q
pip install -r requirements.txt -q
echo "✓ Dependencies installed"

# Setup configuration
if [ ! -f "config/config.yaml" ]; then
    echo "⚙️  Setting up configuration..."
    cp config/config.example.yaml config/config.yaml
    echo "✓ config/config.yaml created (please update with your credentials)"
else
    echo "✓ config/config.yaml already exists"
fi

# Setup environment variables
if [ ! -f ".env" ]; then
    echo "⚙️  Setting up environment variables..."
    cp .env.example .env
    echo "✓ .env created (please update with your credentials)"
else
    echo "✓ .env already exists"
fi

# Create necessary directories
echo "📁 Creating output directories..."
mkdir -p logs
mkdir -p outputs/cypher outputs/reports outputs/validation
mkdir -p data/schemas data/samples data/crosswalks
echo "✓ Directories created"

# Test installation
echo ""
echo "🧪 Testing installation..."
python main.py --help > /dev/null 2>&1
if [ $? -eq 0 ]; then
    echo "✓ Installation test passed"
else
    echo "❌ Installation test failed"
    exit 1
fi

echo ""
echo "=" repeat 60
echo "✅ Setup complete!"
echo ""
echo "📋 Next steps:"
echo "1. Update config/config.yaml with your database credentials"
echo "2. Update .env with your API keys (for Text2Cypher)"
echo "3. Run: python main.py status (to test connections)"
echo "4. Run: python main.py analyze (to analyze schema)"
echo ""
echo "📚 Documentation:"
echo "  - README.md - Project overview"
echo "  - docs/guides/SETUP.md - Detailed setup guide"
echo "  - PROJECT_STRUCTURE.md - Project structure"
echo ""
echo "Happy coding! 🎉"
