# Asset Manager WordPress Plugin Documentation (v1.8.3)

**Plugin Name:** Asset Manager
**Description:** Custom post type for managing assets with history tracking, custom fields, PDF export, and more.
**Version:** 1.8.3
**Author:** Your Name
**Text Domain:** `asset-manager`
**Domain Path:** `/languages`

## Table of Contents

1.  [Overview](#overview)
2.  [Key Features](#key-features)
3.  [Installation](#installation)
4.  [Usage](#usage)
    * [Accessing Asset Manager](#accessing-asset-manager)
    * [Adding a New Asset](#adding-a-new-asset)
    * [Asset Fields Explained](#asset-fields-explained)
    * [Managing Asset Categories](#managing-asset-categories)
    * [Viewing Asset History](#viewing-asset-history)
    * [Asset Dashboard](#asset-dashboard)
    * [Exporting Assets to PDF](#exporting-assets-to-pdf)
    * [Viewing All Assets](#viewing-all-assets)
5.  [For Developers](#for-developers)
    * [Constants](#constants)
    * [Custom Post Type](#custom-post-type)
    * [Custom Taxonomy](#custom-taxonomy)
    * [Meta Fields](#meta-fields)
    * [Action Hooks](#action-hooks)
    * [Filter Hooks](#filter-hooks)
    * [File Structure](#file-structure)
    * [Internationalization](#internationalization)
6.  [Troubleshooting & FAQ](#troubleshooting--faq)
7.  [Changelog (Summary)](#changelog-summary)

## 1. Overview

The Asset Manager plugin provides a robust system for managing physical and digital assets within your WordPress website. It allows you to track detailed information about each asset, categorize them, monitor their status and assignment, view their history, and export data for reporting.

This plugin is ideal for businesses, organizations, or individuals who need to keep an organized inventory of equipment, tools, licenses, or any other items that require tracking.

## 2. Key Features

* **Custom Post Type for Assets:** Dedicated 'Assets' section in the WordPress admin area.
* **Detailed Asset Information:** Track numerous details for each asset (see [Asset Fields Explained](#asset-fields-explained)).
* **Asset Categories:** Organize assets using a custom 'Asset Category' taxonomy.
* **Image Upload:** Associate an image with each asset for easy identification.
* **Comprehensive History Tracking:** Logs all changes made to an asset, including who made the change and when.
* **Status Management:** Predefined statuses (Unassigned, Assigned, Returned, For Repair, Repairing, Archived, Disposed) to track the asset lifecycle.
* **User Assignment:** Assign assets to specific WordPress users.
* **Admin Dashboard:** Visual overview of assets by status, user, and category using charts (powered by Chart.js).
* **PDF Export:** Export a complete list of assets to a PDF document (powered by mPDF).
* **Customizable Admin Columns:** The 'All Assets' list view displays key asset information for quick review.
* **Data Validation:** Ensures required fields are completed and data is in the correct format.
* **Internationalization Ready:** Supports translation into other languages.

## 3. Installation

1.  **Download:** If you have the plugin as a `.zip` file, download it to your computer.
2.  **Upload to WordPress:**
    * Navigate to your WordPress admin dashboard.
    * Go to **Plugins > Add New**.
    * Click the **Upload Plugin** button at the top of the page.
    * Click **Choose File**, select the `it-asset-manager-lite.php` (or the .zip file if you have it packaged) from your computer.
    * Click **Install Now**.
3.  **Activate:** After the plugin is installed, click the **Activate Plugin** button.

Alternatively, if you have direct server access:

1.  Upload the `it-asset-manager-lite.php` file (and any associated folders like `css`, `js`, `languages`, `vendor` if they are separate) to your `wp-content/plugins/` directory. You might want to create a folder like `asset-manager` inside `wp-content/plugins/` and place the file(s) there.
2.  Navigate to the **Plugins** page in your WordPress admin dashboard.
3.  Locate "Asset Manager" in the list and click **Activate**.

**Dependencies:**
* **mPDF Library:** For PDF export functionality. The plugin attempts to load this from a `vendor/autoload.php` file within its directory. Ensure this library is correctly installed if you intend to use the PDF export feature.

## 4. Usage

### Accessing Asset Manager

Once activated, you will find a new menu item labeled **"Assets"** in your WordPress admin sidebar.

* **Assets > All Assets:** View, edit, and manage all existing assets.
* **Assets > Add New:** Add a new asset.
* **Assets > Categories:** Manage asset categories.
* **Assets > Dashboard:** View graphical reports on asset distribution.
* **Assets > Export to PDF:** Access the PDF export functionality.

### Adding a New Asset

1.  Navigate to **Assets > Add New**.
2.  **Title:** While you can enter a title manually, the plugin will automatically generate a title based on the "Asset Tag" (e.g., "Asset: [Asset Tag]") or "Asset #[Post ID]" if the Asset Tag is empty, upon saving.
3.  **Asset Image (Right Sidebar):**
    * Click **Upload Image** to select or upload an image for the asset from the WordPress Media Library.
    * Click **Remove Image** to detach the current image.
4.  **Asset Details (Main Content Area):** Fill in the required and optional fields as described below.
5.  **Category (Right Sidebar or within Asset Details section):** Select an appropriate category for the asset. You can also add new categories from here.
6.  Click **Publish** (or **Save Draft**) to save the asset.

### Asset Fields Explained

The following fields are available in the "Asset Details" meta box when adding or editing an asset. Fields marked with a red asterisk (`*`) are required.

* **Asset Tag `*`:** A unique identifier for the asset (e.g., `COMP-001`, `TOOL-A56`).
* **Model `*`:** The model name or number of the asset (e.g., `Latitude 7400`, `iPhone 15 Pro`).
* **Serial Number `*`:** The manufacturer's serial number.
* **Brand `*`:** The brand or manufacturer of the asset (e.g., `Dell`, `Apple`).
* **Supplier `*`:** The vendor or supplier from whom the asset was acquired.
* **Date Purchased `*`:** The date the asset was purchased. Use the `YYYY-MM-DD` format.
* **Issued To `*`:** Select the WordPress user to whom the asset is currently assigned. Choose "-- Select User --" if it's not assigned to a specific user (though "Unassigned" status is preferred for this).
* **Status `*`:** The current status of the asset. Options include:
    * `Unassigned`
    * `Assigned`
    * `Returned`
    * `For Repair`
    * `Repairing`
    * `Archived`
    * `Disposed`
* **Location `*`:** The physical location of the asset (e.g., `Main Office - Room 101`, `Warehouse Section B`, `Remote Employee - J. Doe`).
* **Description `*`:** A detailed description of the asset, its condition, or any other relevant notes.
* **Category `*` (Dropdown within Asset Details or separate meta box):** The category the asset belongs to.

### Managing Asset Categories

Asset categories help you organize your assets.

1.  Navigate to **Assets > Categories**.
2.  Here you can:
    * **Add a New Asset Category:** Provide a name, slug (optional, WordPress will generate one), parent category (if creating a sub-category), and description.
    * **Edit Existing Categories:** Hover over a category name and click "Edit".
    * **Delete Categories:** Hover over a category name and click "Delete".
    * **Quick Edit:** Make minor changes like name and slug without leaving the list.

### Viewing Asset History

Each asset has a history log that tracks changes made to its details.

1.  Go to **Assets > All Assets**.
2.  Click on the title of the asset (or hover and click "Edit") you want to inspect.
3.  Scroll down to the **"Asset History"** meta box.
4.  The history is displayed in reverse chronological order (most recent changes first), showing the date, the user who made the change (if available), and a description of what was altered.

### Asset Dashboard

The Asset Dashboard provides a visual summary of your assets.

1.  Navigate to **Assets > Dashboard**.
2.  You will see three charts:
    * **Assets by Status:** A pie chart showing the distribution of assets across different statuses.
    * **Assets by User:** A bar or pie chart showing how many assets are assigned to each user.
    * **Assets by Category:** A pie chart showing the distribution of assets across different categories.

### Exporting Assets to PDF

You can export a list of all your assets into a PDF document.

1.  Navigate to **Assets > Export to PDF**.
2.  Click the **"Export All Assets as PDF"** button.
3.  Your browser will download a PDF file (e.g., `assets-YYYY-MM-DD.pdf`).

The PDF includes the following columns:
* Title
* Asset Tag
* Model
* Serial No.
* Brand
* Category
* Location
* Status
* Issued To
* Description

### Viewing All Assets

The "All Assets" screen provides a tabular view of your assets.

1.  Navigate to **Assets > All Assets**.
2.  The table displays the following columns by default:
    * Checkbox (for bulk actions)
    * Title
    * Asset Tag
    * Model
    * Serial Number
    * Brand
    * Category
    * Location
    * Status
    * Issued To
    * Date (Publish Date)
3.  You can sort assets by clicking on column headers (for sortable columns).
4.  Standard WordPress bulk actions (Edit, Move to Trash) are available.

## 5. For Developers

### Constants

The plugin defines the following constants:

* `ASSET_MANAGER_VERSION`: Current version of the plugin (e.g., `'1.8.3'`).
* `ASSET_MANAGER_POST_TYPE`: The slug for the asset custom post type (`'asset'`).
* `ASSET_MANAGER_TAXONOMY`: The slug for the asset category custom taxonomy (`'asset_category'`).
* `ASSET_MANAGER_META_PREFIX`: Prefix for all custom meta field keys (`'_asset_manager_'`).

### Custom Post Type

* **Slug:** `asset` (defined by `ASSET_MANAGER_POST_TYPE`)
* **Public:** `false` (not visible on the front-end by default)
* **Show UI:** `true`
* **Show in Menu:** `true`
* **Supports:** `title` (other fields are handled via meta boxes)
* **Menu Icon:** `dashicons-archive`
* **Show in REST:** `true`

### Custom Taxonomy

* **Slug:** `asset_category` (defined by `ASSET_MANAGER_TAXONOMY`)
* **Associated Post Type:** `asset`
* **Hierarchical:** `true`
* **Show UI:** `true`
* **Show Admin Column:** `true`
* **Show in REST:** `true`

### Meta Fields

All asset-specific data is stored as post meta. The keys use the `ASSET_MANAGER_META_PREFIX`.

* `_asset_manager_asset_tag`
* `_asset_manager_model`
* `_asset_manager_serial_number`
* `_asset_manager_brand`
* `_asset_manager_supplier`
* `_asset_manager_date_purchased` (Stored as `YYYY-MM-DD`)
* `_asset_manager_issued_to` (Stores User ID)
* `_asset_manager_status`
* `_asset_manager_location`
* `_asset_manager_description`
* `_asset_manager_history` (Array of history entries)
* `_asset_image_id` (Stores Attachment ID for the asset image)

The category is handled by WordPress's term relationship tables, but the selected category ID is also temporarily stored in `_asset_manager_asset_category` during post save for validation and history tracking if it changes.

### Action Hooks

The plugin utilizes various WordPress action hooks. Some notable custom actions or specific uses:

* `add_meta_boxes`: Used to add the "Asset Details", "Asset History", and "Asset Image" meta boxes.
* `save_post_asset`: Hooked by `save_asset_meta()` to save custom field data and `save_asset_image()` to save the image ID.
* `admin_enqueue_scripts`: To enqueue admin-specific CSS (`asset-manager.css`) and JavaScript (`asset-manager-admin.js`, `asset-dashboard.js`). Also enqueues `wp_enqueue_media()` for the image uploader.
* `admin_post_am_export_assets_pdf_action`: Handles the PDF export request.
* `admin_notices`: Used to display validation error messages.
* `init`: Registers post type, taxonomy, text domain, and shortcodes (placeholder).
* `register_activation_hook`: Calls the `activate()` method to register post type/taxonomy and flush rewrite rules on plugin activation.

### Filter Hooks

* `manage_asset_posts_columns`: To customize the columns displayed on the "All Assets" list table.
* `manage_asset_posts_custom_column`: To render the content for custom columns.
* `redirect_post_location`: Used to prevent the default "Post updated" message when validation errors occur, allowing custom error notices to be shown instead.

### File Structure (Simplified)

it-asset-manager-lite.php       // Main plugin file/css/asset-manager.css           // Admin styles/js/asset-manager-admin.js      // Admin JavaScript for asset edit screenasset-dashboard.js          // JavaScript for the dashboard charts/languages/asset-manager.pot           // POT file for translations (if generated)asset-manager-xx_XX.po      // Example PO fileasset-manager-xx_XX.mo      // Example MO file/vendor/                          // For third-party libraries like mPDFautoload.php/mpdf/... (mPDF library files) ...
### Internationalization

The plugin is translation-ready.
* **Text Domain:** `asset-manager`
* **Domain Path:** `/languages`
All user-facing strings are wrapped in WordPress translation functions like `__()`, `_e()`, `_x()`, `esc_html__()`, etc.
To translate the plugin:
1.  Use a tool like Poedit.
2.  Create a new translation from the plugin's `.pot` file (if available) or directly from the source code.
3.  Save your translation files as `asset-manager-<locale_code>.po` and `asset-manager-<locale_code>.mo` (e.g., `asset-manager-es_ES.po`) in the `languages` subfolder of the plugin.

## 6. Troubleshooting & FAQ

* **PDF Export Not Working / "mPDF library is missing" error:**
    * Ensure the mPDF library is correctly installed in the `vendor` directory within the plugin's folder structure. If you installed the plugin manually, you might need to run `composer install` in the plugin's root directory if it has a `composer.json` file, or manually place the mPDF library files.
* **Required Fields:**
    * All fields marked with a red asterisk (`*`) in the "Asset Details" section are mandatory. The form cannot be saved if these are empty or invalid.
* **CSS or JS Issues:**
    * Try clearing your browser cache and any caching plugin caches.
    * Check your browser's developer console (usually F12) for JavaScript errors.
* **Plugin Conflicts:**
    * If you experience unexpected behavior, try deactivating other plugins one by one to see if there's a conflict.
* **"Unassigned" Status vs. Empty "Issued To":**
    * While you can leave "Issued To" as "-- Select User --", it's generally better to use the "Unassigned" status to clearly indicate an asset is not currently with a user. The dashboard and reporting might rely on the "Status" field more directly for this.

## 7. Changelog (Summary)

* **1.8.3 (Current):**
    * Added "Location" field to asset details, admin columns, and PDF export.
    * Updated validation and history tracking for the new "Location" field.
* **1.8.2 (Previous):**
    * Prioritized "Model" field to be second in the input form.
    * Added "Unassigned" as a primary status option.
    * Included "Model" field in PDF export.
    * Minor code refinements and bug fixes.
* **(Older versions)**
    * Initial release and subsequent feature enhancements (image upload, dashboard, etc.).

---

This documentation should provide a good starting point for users and developers working with the Asset Manager plugin.
This documentation covers the main aspects of your Asset Manager plugin. You can expand on any section as needed, especially the "For Developers" and "Troubleshooting" parts if you anticipate more complex interactions or common issues. Remember to keep this documentation updated as you add new features or make significant changes to the plugin.