"""Notes service for storing and retrieving notes per card - using Elasticsearch only"""
import logging
from typing import Optional
from elasticsearch_service import (
    check_elasticsearch_connection,
    index_note,
    get_card_by_id_es
)

logger = logging.getLogger(__name__)


def get_note(card_id: str) -> str:
    """Get note for a card from Elasticsearch"""
    try:
        if not check_elasticsearch_connection():
            return ""
        
        from elasticsearch_service import es, INDEX_NOTES
        note_id = f"note_{card_id}"
        try:
            response = es.get(index=INDEX_NOTES, id=note_id)
            # Try to get note_text from metadata first (new format)
            metadata = response["_source"].get("metadata", {})
            if "note_text" in metadata:
                return metadata["note_text"]
            # Fallback: extract from content (old format)
            content = response["_source"].get("content", "")
            note_text = content.split("Company:")[0].split("Person:")[0].split("Industry:")[0].strip()
            return note_text
        except Exception:
            return ""
    except Exception as e:
        logger.error(f"Failed to get note for {card_id}: {e}")
        return ""


def save_note(card_id: str, note: str) -> bool:
    """Save note for a card to Elasticsearch"""
    try:
        if not check_elasticsearch_connection():
            logger.warning("Elasticsearch not available, cannot save note")
            return False
        
        # Get card to determine card_type
        card = get_card_by_id_es(card_id)
        if not card:
            logger.warning(f"Card {card_id} not found, cannot save note")
            return False
        
        # Determine card_type from dict
        if not card:
            logger.error(f"Card {card_id} not found")
            return False
        
        card_type = card.get("card_type", "unknown")
        if card_type == "company":
            card_metadata = {
                "name": card.get("name"),
                "industry": card.get("industry"),
                "location": card.get("location"),
                "description": card.get("description")
            }
        elif card_type == "person":
            card_metadata = {
                "name": card.get("name"),
                "company": card.get("company"),
                "designation": card.get("designation"),
                "education": card.get("education"),
                "location": card.get("location")
            }
        else:
            logger.error(f"Unknown card type for {card_id}")
            return False
        
        # Index note in Elasticsearch
        return index_note(card_id, note, card_type, card_metadata)
    except Exception as e:
        logger.error(f"Failed to save note for {card_id}: {e}")
        return False


def delete_note(card_id: str) -> bool:
    """Delete note for a card from Elasticsearch"""
    try:
        if not check_elasticsearch_connection():
            return False
        
        from elasticsearch_service import es, INDEX_NOTES
        note_id = f"note_{card_id}"
        es.delete(index=INDEX_NOTES, id=note_id, ignore=[404])
        return True
    except Exception as e:
        logger.error(f"Failed to delete note for {card_id}: {e}")
        return False
