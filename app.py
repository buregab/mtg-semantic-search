from flask import Flask, request, jsonify, render_template_string
import weaviate
import os
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Weaviate connection
WEAVIATE_HOST = os.getenv('WEAVIATE_HOST', 'weaviate')
WEAVIATE_PORT = os.getenv('WEAVIATE_PORT', 8080)

def get_weaviate_client():
    """Get Weaviate client connection"""
    return weaviate.connect_to_local(host=WEAVIATE_HOST, port=WEAVIATE_PORT)

@app.route('/')
def index():
    """Main search page"""
    html_template = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>MTG Semantic Search</title>
        <style>
            body { font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; }
            .search-box { width: 100%; padding: 10px; font-size: 16px; margin-bottom: 20px; }
            .card { border: 1px solid #ddd; margin: 10px 0; padding: 15px; border-radius: 5px; display: flex; gap: 15px; align-items: flex-start; }
            .card-image { flex-shrink: 0; width: 150px; }
            .card-image img { width: 100%; border-radius: 4px; object-fit: cover; }
            .card-content { flex: 1; }
            .card-name { font-weight: bold; font-size: 18px; color: #333; }
            .card-type { color: #666; margin: 5px 0; }
            .card-text { margin: 10px 0; }
            .mana-cost { color: #0066cc; font-weight: bold; }
            .power-toughness { color: #cc6600; font-weight: bold; }
            .loading { text-align: center; color: #666; }
        </style>
    </head>
    <body>
        <h1>MTG Card Semantic Search</h1>
        <input type="text" id="searchInput" class="search-box" placeholder="Search for cards... (e.g., 'powerful red dragon', 'blue control spell')" />
        <div id="results"></div>
        
        <script>
            const searchInput = document.getElementById('searchInput');
            const results = document.getElementById('results');
            
            let searchTimeout;
            
            searchInput.addEventListener('input', function() {
                clearTimeout(searchTimeout);
                const query = this.value.trim();
                
                if (query.length < 2) {
                    results.innerHTML = '';
                    return;
                }
                
                searchTimeout = setTimeout(() => {
                    searchCards(query);
                }, 300);
            });
            
            async function searchCards(query) {
                results.innerHTML = '<div class="loading">Searching...</div>';
                
                try {
                    const response = await fetch('/search', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                        },
                        body: JSON.stringify({ query: query })
                    });
                    
                    const data = await response.json();
                    displayResults(data);
                } catch (error) {
                    results.innerHTML = '<div class="loading">Error searching cards</div>';
                }
            }
            
            function displayResults(cards) {
                if (!cards || cards.length === 0) {
                    results.innerHTML = '<div class="loading">No cards found</div>';
                    return;
                }
                
                const html = cards.map(card => `
                    <div class="card">
                        ${card.image_url ? `
                            <div class="card-image">
                                <img src="${card.image_url}" alt="${card.name || 'Card art'}" loading="lazy" onerror="this.parentElement.style.display='none';" />
                            </div>
                        ` : ''}
                        <div class="card-content">
                            <div class="card-name">${card.name || 'Unknown'}</div>
                            <div class="card-type">${card.type || ''}</div>
                            ${card.mana_cost ? `<div class="mana-cost">Cost: ${card.mana_cost}</div>` : ''}
                            ${card.power && card.toughness ? `<div class="power-toughness">${card.power}/${card.toughness}</div>` : ''}
                            ${card.text ? `<div class="card-text">${card.text}</div>` : ''}
                            ${card.flavor ? `<div class="card-text" style="font-style: italic; color: #666;">${card.flavor}</div>` : ''}
                        </div>
                    </div>
                `).join('');
                
                results.innerHTML = html;
            }
        </script>
    </body>
    </html>
    """
    return render_template_string(html_template)

@app.route('/search', methods=['POST'])
def search_cards():
    """Search for cards using semantic search"""
    try:
        data = request.get_json()
        query = data.get('query', '').strip()
        
        if not query:
            return jsonify({'error': 'Query is required'}), 400
        
        # Connect to Weaviate and search
        client = get_weaviate_client()
        
        try:
            cards = client.collections.use("Cards")
            response = cards.query.near_text(
                query=query,
                limit=5,
                distance=0.7
            )
            
            # Format results
            results = []
            for obj in response.objects:
                card_data = obj.properties
                results.append(card_data)
            
            return jsonify(results)
            
        finally:
            client.close()
            
    except Exception as e:
        logger.error(f"Search error: {str(e)}", exc_info=True)
        return jsonify({'error': str(e)}), 500

@app.route('/health')
def health():
    """Health check endpoint"""
    try:
        client = get_weaviate_client()
        client.close()
        return jsonify({'status': 'healthy', 'weaviate': 'connected'})
    except Exception as e:
        logger.error(f"Health check error: {str(e)}", exc_info=True)
        return jsonify({'status': 'unhealthy', 'error': str(e)}), 500

if __name__ == '__main__':
    logger.info(f"Starting Flask app on port 5000")
    app.run(host='0.0.0.0', port=5000, debug=True)
