#!/usr/bin/env python3
# /// script
# dependencies = [
#   "mcp[cli]>=1.7.0,<2.0.0",
#   "python-frontmatter>=1.0.0,<2.0.0"
# ]
# ///

import os
import pathlib
from typing import Dict, Any, Optional, Tuple, List, Union
from collections import Counter
from datetime import datetime as dt # Alias for datetime

import frontmatter # Handles reading and writing frontmatter
from yaml import YAMLError # To catch parsing errors specifically

from mcp.server.fastmcp import FastMCP

mcp_server = FastMCP(
    name="HugoFrontmatterMCP",
    description="MCP server for Hugo frontmatter. Tools for specific fields, list fields (tags, images), and batch operations. Expects absolute paths."
)

# --- Helper Functions ---

def _load_post(file_path_str: str) -> Tuple[Optional[frontmatter.Post], Optional[Dict[str, Any]]]:
    """Loads a post using python-frontmatter. Expects an absolute file path.
    Returns (post_object, None) on success, or (None, error_dict) on failure.
    """
    file_path = pathlib.Path(file_path_str)
    if not file_path.is_absolute():
        return None, {"error": f"Path must be absolute: {file_path_str}", "file_path": file_path_str}
    if not file_path.is_file():
        return None, {"error": f"File not found: {file_path_str}", "file_path": file_path_str}
    try:
        post = frontmatter.load(file_path)
        return post, None
    except FileNotFoundError:
        return None, {"error": f"File not found during load: {file_path_str}", "file_path": file_path_str}
    except YAMLError as e:
        return None, {"error": f"YAML parsing error in frontmatter: {str(e)}", "file_path": file_path_str}
    except Exception as e:
        return None, {"error": f"Failed to load or parse file: {str(e)}", "file_path": file_path_str}

def _save_post(file_path_str: str, post: frontmatter.Post) -> Optional[Dict[str, Any]]:
    """Saves a post object back to its file. Expects an absolute file path.
    Returns None on success, or error_dict on failure.
    """
    file_path = pathlib.Path(file_path_str)
    if not file_path.is_absolute():
        return {"error": f"Path for saving must be absolute: {file_path_str}", "file_path": file_path_str}
    try:
        frontmatter.dump(post, file_path_str)
        return None
    except IOError as e:
        return {"error": f"Failed to write file: {str(e)}", "file_path": file_path_str}
    except Exception as e:
        return {"error": f"An unexpected error occurred while saving: {str(e)}", "file_path": file_path_str}

# --- MCP Tools (Single File Operations) ---

@mcp_server.tool()
def get_frontmatter(file_path: str) -> Dict[str, Any]:
    """Reads and returns the entire YAML frontmatter from the specified Markdown file. Expects an absolute file path."""
    post, error = _load_post(file_path)
    if error:
        return error
    if post:
        return {"file_path": file_path, "frontmatter": post.metadata}
    return {"error": "Unknown error loading post", "file_path": file_path}

@mcp_server.tool()
def get_field(file_path: str, field_name: str) -> Dict[str, Any]:
    """Retrieves the value of a specific field from the frontmatter of a file. Expects an absolute file path."""
    post, error = _load_post(file_path)
    if error:
        return error
    if post:
        if field_name in post.metadata:
            return {"file_path": file_path, "field": field_name, "value": post.metadata[field_name], "exists": True}
        else:
            return {"file_path": file_path, "field": field_name, "exists": False, "value": None}
    return {"error": "Unknown error loading post", "file_path": file_path}

def _set_specific_field(file_path: str, field_name: str, field_value: Any, expected_type: type = None) -> Dict[str, Any]:
    """Internal helper to set a specific field after type checking."""
    if expected_type is not None and not isinstance(field_value, expected_type):
        return {"error": f"Value for '{field_name}' must be of type {expected_type.__name__}. Got {type(field_value).__name__}.", "file_path": file_path}

    post, load_error = _load_post(file_path)
    if load_error:
        return load_error
    if not post:
         return {"error": "Unknown error loading post, post object is None.", "file_path": file_path}

    post.metadata[field_name] = field_value
    save_error = _save_post(file_path, post)
    if save_error:
        return save_error
    
    return {
        "file_path": file_path,
        "field_name": field_name,
        "new_value": field_value,
        "message": f"Field '{field_name}' updated and file saved successfully.",
        "updated_frontmatter": post.metadata
    }

@mcp_server.tool()
def set_title(file_path: str, title: str) -> Dict[str, Any]:
    """Sets the 'title' (string) in the frontmatter. Expects an absolute file path."""
    return _set_specific_field(file_path, "title", title, str)

@mcp_server.tool()
def set_date(file_path: str, date_value: str) -> Dict[str, Any]:
    """Sets the 'date' (string, e.g., YYYY-MM-DD) in the frontmatter. Expects an absolute file path."""
    return _set_specific_field(file_path, "date", date_value, str)

@mcp_server.tool()
def set_publish_date(file_path: str, publish_date_value: str) -> Dict[str, Any]:
    """Sets the 'publishDate' (string, e.g., YYYY-MM-DD) in the frontmatter. Expects an absolute file path."""
    return _set_specific_field(file_path, "publishDate", publish_date_value, str)

@mcp_server.tool()
def set_description(file_path: str, description: str) -> Dict[str, Any]:
    """Sets the 'description' (string) in the frontmatter. Expects an absolute file path."""
    return _set_specific_field(file_path, "description", description, str)

@mcp_server.tool()
def set_draft_status(file_path: str, draft_status: bool) -> Dict[str, Any]:
    """Sets the 'draft' status (boolean) in the frontmatter. Expects an absolute file path."""
    return _set_specific_field(file_path, "draft", draft_status, bool)

def _modify_list_field(action: str, file_path: str, field_name: str, item_value: str) -> Dict[str, Any]:
    """Helper to add or remove an item from a list field (e.g., tags, images)."""
    post, load_error = _load_post(file_path)
    if load_error:
        return load_error
    if not post:
        return {"error": "Unknown error loading post", "file_path": file_path}

    current_list = post.metadata.get(field_name)
    if current_list is None:
        current_list = []
    elif not isinstance(current_list, list):
        if isinstance(current_list, str):
            current_list = [current_list] 
        else:
            return {"error": f"Field '{field_name}' exists but is not a list (type: {type(current_list).__name__}). Cannot modify.", "file_path": file_path}
    
    made_change = False
    if action == "add":
        if item_value not in current_list:
            current_list.append(item_value)
            made_change = True
        else:
            return {"message": f"Item '{item_value}' already exists in '{field_name}'. No changes made.", "file_path": file_path, field_name: current_list, "updated_frontmatter": post.metadata}
    elif action == "remove":
        if item_value in current_list:
            current_list.remove(item_value)
            made_change = True
        else:
            return {"message": f"Item '{item_value}' not found in '{field_name}'. No changes made.", "file_path": file_path, field_name: current_list, "updated_frontmatter": post.metadata}
    else:
        return {"error": "Invalid action for _modify_list_field", "file_path": file_path}

    if not made_change: # Should be caught by specific messages above, but as a safeguard.
        return {"message": "No effective change made.", "file_path": file_path, field_name: current_list, "updated_frontmatter": post.metadata}

    post.metadata[field_name] = current_list
    save_error = _save_post(file_path, post)
    if save_error:
        return save_error

    action_verb = "added" if action == "add" else "removed"
    return {
        "file_path": file_path,
        "field_name": field_name,
        "action": action,
        "item_value": item_value,
        "message": f"Item '{item_value}' {action_verb} for field '{field_name}'. File saved.",
        "updated_frontmatter": post.metadata
    }

@mcp_server.tool()
def add_tag(file_path: str, tag_to_add: str) -> Dict[str, Any]:
    """Adds a tag to the 'tags' list in the frontmatter. Expects an absolute file path."""
    if not isinstance(tag_to_add, str) or not tag_to_add.strip():
        return {"error": "Tag to add must be a non-empty string.", "file_path": file_path, "tag_to_add": tag_to_add}
    return _modify_list_field(action="add", file_path=file_path, field_name="tags", item_value=tag_to_add)

@mcp_server.tool()
def remove_tag(file_path: str, tag_to_remove: str) -> Dict[str, Any]:
    """Removes a tag from the 'tags' list in the frontmatter. Expects an absolute file path."""
    if not isinstance(tag_to_remove, str) or not tag_to_remove.strip():
        return {"error": "Tag to remove must be a non-empty string.", "file_path": file_path, "tag_to_remove": tag_to_remove}
    return _modify_list_field(action="remove", file_path=file_path, field_name="tags", item_value=tag_to_remove)

@mcp_server.tool()
def add_image(file_path: str, image_path_to_add: str) -> Dict[str, Any]:
    """Adds an image path to the 'images' list in the frontmatter. Expects an absolute file path for the post."""
    if not isinstance(image_path_to_add, str) or not image_path_to_add.strip():
        return {"error": "Image path to add must be a non-empty string.", "file_path": file_path, "image_path_to_add": image_path_to_add}
    return _modify_list_field(action="add", file_path=file_path, field_name="images", item_value=image_path_to_add)

@mcp_server.tool()
def remove_image(file_path: str, image_path_to_remove: str) -> Dict[str, Any]:
    """Removes an image path from the 'images' list in the frontmatter. Expects an absolute file path for the post."""
    if not isinstance(image_path_to_remove, str) or not image_path_to_remove.strip():
        return {"error": "Image path to remove must be a non-empty string.", "file_path": file_path, "image_path_to_remove": image_path_to_remove}
    return _modify_list_field(action="remove", file_path=file_path, field_name="images", item_value=image_path_to_remove)

# --- MCP Tools (Batch Directory Operations) ---

@mcp_server.tool()
def list_tags_in_directory(directory_path_str: str, recursive: bool = True) -> Dict[str, Any]:
    """Scans .md files in a directory for 'tags' in their frontmatter and returns tag counts. Expects an absolute directory path."""
    directory_path = pathlib.Path(directory_path_str)
    if not directory_path.is_absolute():
        return {"error": f"Directory path must be absolute: {directory_path_str}", "directory_path": directory_path_str}
    if not directory_path.is_dir():
        return {"error": f"Directory not found: {directory_path_str}", "directory_path": directory_path_str}

    tag_counter = Counter()
    file_pattern = "**/*.md" if recursive else "*.md"
    files_processed = 0
    files_with_tags = 0

    for md_file_path_obj in directory_path.glob(file_pattern):
        if md_file_path_obj.is_file():
            files_processed += 1
            post, load_error = _load_post(str(md_file_path_obj))
            if load_error:
                print(f"Skipping file (list_tags_in_directory) due to error: {str(md_file_path_obj)} - {load_error['error']}") 
                continue 
            
            if post and isinstance(post.metadata.get('tags'), list):
                files_with_tags +=1
                for tag in post.metadata['tags']:
                    if isinstance(tag, str):
                        tag_counter[tag] += 1
                    else:
                        print(f"Warning (list_tags_in_directory): Non-string tag found in {str(md_file_path_obj)}: {tag}")

    return {
        "directory_path": directory_path_str,
        "recursive": recursive,
        "files_processed": files_processed,
        "files_with_tags": files_with_tags,
        "tag_counts": dict(tag_counter)
    }

@mcp_server.tool()
def find_posts_by_tag(directory_path_str: str, tag_to_find: str, recursive: bool = True) -> Dict[str, Any]:
    """Finds all posts containing a specific tag. Expects an absolute directory path."""
    directory_path = pathlib.Path(directory_path_str)
    if not directory_path.is_absolute():
        return {"error": f"Directory path must be absolute: {directory_path_str}", "directory_path": directory_path_str}
    if not directory_path.is_dir():
        return {"error": f"Directory not found: {directory_path_str}", "directory_path": directory_path_str}
    if not isinstance(tag_to_find, str) or not tag_to_find.strip():
        return {"error": "Tag to find must be a non-empty string.", "tag_to_find": tag_to_find}

    matching_files = []
    file_pattern = "**/*.md" if recursive else "*.md"
    files_processed = 0

    for md_file_path_obj in directory_path.glob(file_pattern):
        if md_file_path_obj.is_file():
            files_processed += 1
            post, load_error = _load_post(str(md_file_path_obj))
            if load_error:
                print(f"Skipping file (find_posts_by_tag) due to error: {str(md_file_path_obj)} - {load_error['error']}")
                continue
            
            if post and isinstance(post.metadata.get('tags'), list):
                if tag_to_find in post.metadata['tags']:
                    matching_files.append(str(md_file_path_obj))
    
    return {
        "directory_path": directory_path_str,
        "tag_searched": tag_to_find,
        "recursive": recursive,
        "files_processed": files_processed,
        "matching_files": matching_files
    }

@mcp_server.tool()
def rename_tag_in_directory(directory_path_str: str, old_tag: str, new_tag: str, recursive: bool = True) -> Dict[str, Any]:
    """Renames a tag in all posts within a directory. Expects absolute paths for directory and tags as non-empty strings."""
    directory_path = pathlib.Path(directory_path_str)
    if not directory_path.is_absolute():
        return {"error": f"Directory path must be absolute: {directory_path_str}"}
    if not directory_path.is_dir():
        return {"error": f"Directory not found: {directory_path_str}"}
    if not (isinstance(old_tag, str) and old_tag.strip()):
        return {"error": "Old tag must be a non-empty string.", "old_tag": old_tag}
    if not (isinstance(new_tag, str) and new_tag.strip()):
        return {"error": "New tag must be a non-empty string.", "new_tag": new_tag}
    if old_tag == new_tag:
        return {"message": "Old and new tags are the same. No changes will be made.", "old_tag": old_tag, "new_tag": new_tag}

    modified_files_paths = []
    files_scanned = 0
    individual_errors = []
    file_pattern = "**/*.md" if recursive else "*.md"

    for md_file_path_obj in directory_path.glob(file_pattern):
        if md_file_path_obj.is_file():
            files_scanned += 1
            post, load_error = _load_post(str(md_file_path_obj))
            if load_error:
                load_error["file_path"] = str(md_file_path_obj) # Ensure file_path is in error dict
                individual_errors.append(load_error)
                print(f"Skipping file (rename_tag) due to load error: {str(md_file_path_obj)}")
                continue

            if post and isinstance(post.metadata.get('tags'), list):
                tags_list = post.metadata['tags']
                made_change = False
                if old_tag in tags_list:
                    # Remove all instances of old_tag and add new_tag if not present
                    tags_list = [t for t in tags_list if t != old_tag]
                    if new_tag not in tags_list:
                        tags_list.append(new_tag)
                    post.metadata['tags'] = tags_list
                    made_change = True
                
                if made_change:
                    save_error = _save_post(str(md_file_path_obj), post)
                    if save_error:
                        save_error["file_path"] = str(md_file_path_obj) # Ensure file_path is in error dict
                        individual_errors.append(save_error)
                        print(f"Error saving file (rename_tag): {str(md_file_path_obj)}")
                    else:
                        modified_files_paths.append(str(md_file_path_obj))
            elif post and old_tag in str(post.metadata.get('tags', '')): # Handle single tag as string
                 if post.metadata.get('tags') == old_tag:
                    post.metadata['tags'] = [new_tag]
                    save_error = _save_post(str(md_file_path_obj), post)
                    if save_error:
                        individual_errors.append(save_error)
                    else:
                        modified_files_paths.append(str(md_file_path_obj))

    return {
        "directory_path": directory_path_str,
        "old_tag": old_tag,
        "new_tag": new_tag,
        "recursive": recursive,
        "files_scanned": files_scanned,
        "modified_files": modified_files_paths,
        "errors": individual_errors
    }

@mcp_server.tool()
def validate_date_formats(
    directory_path_str: str, 
    field_name: str = "date", 
    expected_format_str: str = "%Y-%m-%d", 
    recursive: bool = True
) -> Dict[str, Any]:
    """Validates date formats in frontmatter. Expects an absolute directory path."""
    directory_path = pathlib.Path(directory_path_str)
    if not directory_path.is_absolute():
        return {"error": f"Directory path must be absolute: {directory_path_str}"}
    if not directory_path.is_dir():
        return {"error": f"Directory not found: {directory_path_str}"}

    invalid_dates_info = []
    files_scanned = 0
    files_with_field_count = 0
    file_pattern = "**/*.md" if recursive else "*.md"

    for md_file_path_obj in directory_path.glob(file_pattern):
        if md_file_path_obj.is_file():
            files_scanned += 1
            post, load_error = _load_post(str(md_file_path_obj))
            if load_error:
                print(f"Skipping file (validate_date) due to error: {str(md_file_path_obj)} - {load_error['error']}")
                invalid_dates_info.append({
                    "file_path": str(md_file_path_obj),
                    "value": "N/A - Load Error",
                    "error": f"File load error: {load_error['error']}"
                })
                continue

            if post and field_name in post.metadata:
                files_with_field_count += 1
                date_value = post.metadata[field_name]
                if isinstance(date_value, str):
                    try:
                        dt.strptime(date_value, expected_format_str)
                    except ValueError as e:
                        invalid_dates_info.append({
                            "file_path": str(md_file_path_obj),
                            "value": date_value,
                            "error": str(e)
                        })
                elif isinstance(date_value, dt): # If it's already a datetime object (less likely from raw frontmatter but possible)
                    # It inherently has a valid format internally if it's a datetime object
                    pass 
                else:
                    invalid_dates_info.append({
                        "file_path": str(md_file_path_obj),
                        "value": str(date_value), # Convert to string for reporting if not string or datetime
                        "error": f"Field value is not a string or date object (type: {type(date_value).__name__})"
                    })
            # If field doesn't exist, it's not invalid for this validation, just missing.

    return {
        "directory_path": directory_path_str,
        "field_name_validated": field_name,
        "expected_format": expected_format_str,
        "recursive": recursive,
        "files_scanned": files_scanned,
        "files_with_field": files_with_field_count,
        "invalid_date_entries": invalid_dates_info
    }


if __name__ == "__main__":
    print(f"Starting Hugo Frontmatter MCP server... Accessible via mcp[cli]. Expects absolute paths.")
    mcp_server.run() 