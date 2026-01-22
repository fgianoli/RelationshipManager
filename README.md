![Relationship Manager Icon](https://raw.githubusercontent.com/fgianoli/RelationshipManager/refs/heads/main/relationManager.png)


# QGIS Relations Management Plugin

The **QGIS Relations Management Plugin** is a powerful tool designed to simplify the handling and management of 1:N relationships within a QGIS project. It provides an intuitive interface for viewing, modifying, duplicating, deleting, and exporting project relationships. This plugin is especially useful for managing complex geospatial data that involve linked layers, enabling users to maintain relational integrity and flexibility.

Imagine you're sitting in a garden, surrounded by a field of flowers, and you pick up a daisy—a simple, elegant flower with a bright yellow center and delicate white petals. As you hold it, you start to realize that this little flower can teach us something profound about relationships, not just in nature, but in the world of data and connections. 
At the heart of the daisy is its central disk, the core that holds everything together. In the same way, in a one-to-many (1:N) relationship, there's always one central entity that serves as the anchor point. Picture this as the "1" in the 1:N structure, just like the daisy's center, which stands alone but connects to many.
Now, look at the petals—they radiate from the center, each one distinct yet connected to that same core. The petals represent the "many," the elements that branch out from that single, central entity. In a relationship, these might be different data points or connections, all linked to that one source, just like the petals are linked to the daisy's heart.
What makes the daisy such a perfect visual metaphor is its simplicity. The structure is clear: one center, many petals. This clarity makes it easy to grasp the idea of a one-to-many relationship—how one entity can be related to many others, each distinct but still part of the same whole. Just as no petal exists on its own without the center, in a 1:N relationship, the "many" are always tied back to that central point.
In this way, the daisy, with its humble beauty, offers a natural, intuitive example of how connections work in the world of data. Its very form speaks to the elegance of relationships—one to many, all part of a single system, just like the petals and the center of the daisy.

## Key Features

- **View Relationships:** Easily browse and visualize all the 1:N relationships present in your QGIS project. Each relationship shows the parent layer, child layer, and the key fields that form the relationship.

- **Modify Relationships:** Modify existing relationships by changing the parent layer, child layer, or the key fields, without the need to recreate them from scratch. This helps maintain consistency while allowing quick updates to project data.

- **Duplicate Relationships:** Create a copy of an existing relationship under a new name, ideal for scenarios where relationships have similar structures but need slight variations.

- **Delete Relationships:** Safely delete unnecessary or outdated relationships directly from the plugin interface, freeing up your project from redundant relations.

- **Export Relationships:** Export all project relationships into a JSON file for easy sharing or backup. This feature is useful for collaboration and version control in larger projects.

- **Import Relationships:** Load relationships from a JSON file into your project, allowing for easy restoration or transfer of relational configurations between projects.

- **View Relationship History:** Track and view the history of changes made to relationships, providing a clear audit trail and the ability to roll back to previous versions when necessary.

## Supported Key Field Types

The plugin supports all QGIS field types as relationship keys, including:
- Integer
- String / Text
- UUID
- And more...

## Why Use This Plugin?

Managing 1:N relationships in a QGIS project can be cumbersome, especially when dealing with large datasets or projects involving multiple layers. This plugin streamlines the process, making it easier to maintain, update, and share relationships between layers, all from a centralized and user-friendly interface. Whether you're working on urban planning, environmental monitoring, or any other geospatial project, this plugin helps maintain the integrity of your data relationships efficiently.

## Changelog

### Version 2.0
This release addresses three issues reported by users and introduces several improvements.

**Bug Fixes:**

The first fix resolves the "Key fields not found" error that occurred when using UUID or string fields as relationship keys. The problem was caused by an incorrect parameter order in the QGIS API call.

The second fix ensures the plugin correctly reads existing relations when opening a project. Previously, relations already defined in QGIS projects were not visible in the plugin interface.

The third fix handles project switching properly. Before this update, when users created a new project or opened a different one, the plugin continued showing relations from the previous project. Now the plugin listens to QGIS project signals and refreshes the list automatically.

**Improvements:**

Error messages are now more informative. When a key field is not found, the plugin displays which field is missing and shows all available fields in the layer.

The create and edit dialogs now feature dynamic field selection - when you change the layer, the field dropdown updates immediately to show the correct fields.

A validation check has been added before creating relations. If something is misconfigured, the plugin warns you before adding an invalid relation. Existing invalid relations are now clearly marked with an "(INVALID)" label in the list.

The Help tab has been completely rewritten with step-by-step guides, a practical example, a troubleshooting section, and best practices for managing relationships.

### Version 1.1
- Added the Help section

### Version 1.0
- Initial release

## License

This plugin is released under the GPL v3 license.
