import os
import zipfile
import textwrap

# --- File Contents ---

# Main Plugin File: asset-manager.php
asset_manager_php_content = """<?php
/**
 * Plugin Name: Asset Manager (MVC)
 * Description: Custom post type for managing assets with history tracking, custom fields, PDF export, and more (MVC Structure).
 * Version: 1.9.0
 * Author: Your Name
 * Text Domain: asset-manager-mvc
 * Domain Path: /languages
 */

if (!defined('ABSPATH')) exit; // Exit if accessed directly

// --- Constants ---
define('ASSET_MANAGER_MVC_VERSION', '1.9.0');
define('ASSET_MANAGER_MVC_POST_TYPE', 'asset_mvc');
define('ASSET_MANAGER_MVC_TAXONOMY', 'asset_category_mvc');
define('ASSET_MANAGER_MVC_META_PREFIX', '_asset_manager_mvc_');
define('ASSET_MANAGER_MVC_PATH', plugin_dir_path(__FILE__));
define('ASSET_MANAGER_MVC_URL', plugin_dir_url(__FILE__));

// --- Autoloader (Simplified for example) ---
// In a real plugin, use a PSR-4 autoloader (e.g., via Composer)
require_once ASSET_MANAGER_MVC_PATH . 'includes/core/class-plugin-core.php';
require_once ASSET_MANAGER_MVC_PATH . 'includes/models/class-asset-model.php';
require_once ASSET_MANAGER_MVC_PATH . 'includes/controllers/class-setup-controller.php';
require_once ASSET_MANAGER_MVC_PATH . 'includes/controllers/class-asset-controller.php';
require_once ASSET_MANAGER_MVC_PATH . 'includes/controllers/class-dashboard-controller.php';
require_once ASSET_MANAGER_MVC_PATH . 'includes/controllers/class-export-controller.php';
// Add other controllers and models as needed

/**
 * Initializes the plugin.
 *
 * Creates an instance of the Plugin_Core class and runs it.
 */
function asset_manager_mvc_run() {
    $plugin_core = new AssetManagerMvc\\Core\\Plugin_Core();
    $plugin_core->run();
}
asset_manager_mvc_run();

/**
 * Activation hook.
 */
function asset_manager_mvc_activate() {
    // Instantiate SetupController directly or through Plugin_Core if preferred for activation tasks
    $setup_controller = new AssetManagerMvc\\Controllers\\Setup_Controller();
    $setup_controller->activate();
    flush_rewrite_rules(); // Important after CPT and taxonomy registration
}
register_activation_hook(__FILE__, 'asset_manager_mvc_activate');

/**
 * Deactivation hook.
 * (Optional: Add any cleanup logic here)
 */
function asset_manager_mvc_deactivate() {
    flush_rewrite_rules();
}
register_deactivation_hook(__FILE__, 'asset_manager_mvc_deactivate');
"""

# Core Class: includes/core/class-plugin-core.php
plugin_core_php_content = """<?php
// File: includes/core/class-plugin-core.php

namespace AssetManagerMvc\\Core;

use AssetManagerMvc\\Controllers\\Setup_Controller;
use AssetManagerMvc\\Controllers\\Asset_Controller;
use AssetManagerMvc\\Controllers\\Dashboard_Controller;
use AssetManagerMvc\\Controllers\\Export_Controller;
use AssetManagerMvc\\Models\\Asset_Model;

if (!defined('ABSPATH')) exit;

/**
 * Plugin_Core Class
 *
 * Orchestrates the plugin's controllers and initializes hooks.
 */
class Plugin_Core {

    /**
     * Asset Model instance.
     * @var Asset_Model
     */
    private $asset_model;

    /**
     * Constructor.
     * Initializes models.
     */
    public function __construct() {
        $this->asset_model = new Asset_Model();
    }

    /**
     * Runs the plugin by initializing controllers and registering hooks.
     */
    public function run() {
        $this->load_dependencies();
        $this->initialize_controllers();
    }

    /**
     * Loads plugin text domain.
     * This is typically hooked to 'plugins_loaded' or 'init'.
     */
    private function load_dependencies() {
        add_action('plugins_loaded', [$this, 'load_textdomain']);
    }

    /**
     * Loads the plugin text domain for translation.
     */
    public function load_textdomain() {
        load_plugin_textdomain(
            'asset-manager-mvc',
            false,
            dirname(plugin_basename(ASSET_MANAGER_MVC_PATH)) . '/languages/'
        );
    }

    /**
     * Initializes all controllers and registers their hooks.
     */
    private function initialize_controllers() {
        $setup_controller = new Setup_Controller();
        $setup_controller->register_hooks();

        // Pass the model to controllers that need it
        $asset_controller = new Asset_Controller($this->asset_model);
        $asset_controller->register_hooks();

        $dashboard_controller = new Dashboard_Controller($this->asset_model);
        $dashboard_controller->register_hooks();

        $export_controller = new Export_Controller($this->asset_model);
        $export_controller->register_hooks();
    }
}
"""

# Model Class: includes/models/class-asset-model.php
asset_model_php_content = """<?php
// File: includes/models/class-asset-model.php

namespace AssetManagerMvc\\Models;

if (!defined('ABSPATH')) exit;

/**
 * Asset_Model Class
 *
 * Handles data operations for assets.
 */
class Asset_Model {

    private $fields = [
        'asset_tag', 'model', 'serial_number', 'brand', 'supplier',
        'date_purchased', 'issued_to', 'status', 'description'
    ];

    private $status_options = ['Unassigned', 'Assigned', 'Returned', 'For Repair', 'Repairing', 'Archived', 'Disposed'];

    /**
     * Get the defined asset fields.
     * @return array
     */
    public function get_fields() {
        return $this->fields;
    }

    /**
     * Get the defined status options.
     * @return array
     */
    public function get_status_options() {
        return $this->status_options;
    }

    /**
     * Get field labels for display.
     * @return array
     */
    public function get_field_labels() {
        return [
            'asset_tag'     => __('Asset Tag', 'asset-manager-mvc'),
            'serial_number' => __('Serial Number', 'asset-manager-mvc'),
            'brand'         => __('Brand', 'asset-manager-mvc'),
            'model'         => __('Model', 'asset-manager-mvc'),
            'supplier'      => __('Supplier', 'asset-manager-mvc'),
            'date_purchased'=> __('Date Purchased', 'asset-manager-mvc'),
            'issued_to'     => __('Issued To', 'asset-manager-mvc'),
            'status'        => __('Status', 'asset-manager-mvc'),
            'description'   => __('Description', 'asset-manager-mvc'),
            ASSET_MANAGER_MVC_META_PREFIX . 'asset_category' => __('Category', 'asset-manager-mvc'),
        ];
    }

    /**
     * Retrieves all meta data for a given asset.
     * @param int $post_id The ID of the asset post.
     * @return array An array of meta values.
     */
    public function get_asset_meta($post_id) {
        $meta_values = [];
        $all_meta = get_post_meta($post_id);
        foreach ($this->fields as $field_key) {
            $meta_key_with_prefix = ASSET_MANAGER_MVC_META_PREFIX . $field_key;
            $meta_values[$field_key] = isset($all_meta[$meta_key_with_prefix][0]) ? $all_meta[$meta_key_with_prefix][0] : '';
        }
        return $meta_values;
    }

    /**
     * Validates asset data from a form submission.
     * @param array $form_data Data from $_POST.
     * @return array An array of error messages. Empty if no errors.
     */
    public function validate_asset_data(array $form_data): array {
        $errors = [];
        $field_labels = $this->get_field_labels();

        foreach ($this->fields as $field_key) {
            $post_field_key = ASSET_MANAGER_MVC_META_PREFIX . $field_key;
            $value = isset($form_data[$post_field_key]) ? trim($form_data[$post_field_key]) : '';

            if ($field_key === 'date_purchased') {
                if (empty($value)) {
                    $errors[] = sprintf(__('The %s field is required.', 'asset-manager-mvc'), $field_labels[$field_key]);
                } else {
                    $date = \\DateTime::createFromFormat('Y-m-d', $value);
                    if (!$date || $date->format('Y-m-d') !== $value) {
                        $errors[] = sprintf(__('The %s field has an invalid date format. Please use YYYY-MM-DD.', 'asset-manager-mvc'), $field_labels[$field_key]);
                    }
                }
            } elseif ($field_key === 'status') {
                 if ($value === '') {
                     $errors[] = sprintf(__('The %s field is required; please select a status.', 'asset-manager-mvc'), $field_labels[$field_key]);
                 } elseif (!in_array($value, $this->status_options, true)) {
                     $errors[] = sprintf(__('Invalid value selected for the %s field.', 'asset-manager-mvc'), $field_labels[$field_key]);
                 }
            } elseif (empty($value) && $value !== '0') { // Allow '0' for fields that might legitimately be 0
                if ($field_key === 'issued_to' && $form_data[$post_field_key] === '') { // Specifically check for empty select
                    $errors[] = sprintf(__('The %s field is required; please select a user.', 'asset-manager-mvc'), $field_labels[$field_key]);
                } elseif ($field_key !== 'issued_to') { // Other fields
                    $errors[] = sprintf(__('The %s field is required.', 'asset-manager-mvc'), $field_labels[$field_key]);
                }
            }
        }

        $category_post_key = ASSET_MANAGER_MVC_META_PREFIX . 'asset_category';
        $category_value = isset($form_data[$category_post_key]) ? $form_data[$category_post_key] : '';
        if (empty($category_value)) {
            $errors[] = sprintf(__('The %s field is required; please select a category.', 'asset-manager-mvc'), $field_labels[$category_post_key]);
        }
        return $errors;
    }

    /**
     * Saves asset meta data and updates history.
     * @param int $post_id The ID of the asset post.
     * @param array $data The data to save (typically from $_POST).
     * @return array Changes made for history logging.
     */
    public function save_asset_data($post_id, array $data) {
        $changes = [];
        $current_history = get_post_meta($post_id, ASSET_MANAGER_MVC_META_PREFIX . 'history', true) ?: [];
        if (!is_array($current_history)) $current_history = [];
        
        $field_labels = $this->get_field_labels();

        foreach ($this->fields as $field_key) {
            $meta_key = ASSET_MANAGER_MVC_META_PREFIX . $field_key;
            $new_value_raw = isset($data[$meta_key]) ? $data[$meta_key] : null;
            $old_value = get_post_meta($post_id, $meta_key, true);
            $new_value_sanitized = '';

            switch ($field_key) {
                case 'description':
                    $new_value_sanitized = sanitize_textarea_field($new_value_raw);
                    break;
                case 'date_purchased':
                    if (is_string($new_value_raw)) {
                        $date = \\DateTime::createFromFormat('Y-m-d', $new_value_raw);
                        $new_value_sanitized = ($date && $date->format('Y-m-d') === $new_value_raw) ? $new_value_raw : '';
                    } else {
                        $new_value_sanitized = '';
                    }
                    break;
                case 'issued_to':
                    $new_value_sanitized = absint($new_value_raw);
                    break;
                case 'status':
                    $new_value_sanitized = in_array($new_value_raw, $this->status_options, true) ? sanitize_text_field($new_value_raw) : $this->status_options[0];
                    break;
                default:
                    $new_value_sanitized = sanitize_text_field($new_value_raw);
                    break;
            }

            $old_value_comparable = ($field_key === 'issued_to') ? absint($old_value) : trim((string)$old_value);
            $new_value_comparable = ($field_key === 'issued_to') ? $new_value_sanitized : trim((string)$new_value_sanitized);


            if ($new_value_comparable !== $old_value_comparable) {
                update_post_meta($post_id, $meta_key, $new_value_sanitized);
                $label = $field_labels[$field_key];

                if ($field_key === 'description') {
                    $changes[] = sprintf(esc_html__('%1$s changed.', 'asset-manager-mvc'), esc_html($label));
                } elseif ($field_key === 'issued_to') {
                    $old_user_display = __('Unassigned', 'asset-manager-mvc');
                    if (!empty($old_value_comparable)) {
                        $old_user_data = get_userdata($old_value_comparable);
                        $old_user_display = $old_user_data ? $old_user_data->display_name : sprintf(__('Unknown User (ID: %s)', 'asset-manager-mvc'), $old_value_comparable);
                    }
                    $new_user_display = __('Unassigned', 'asset-manager-mvc');
                    if (!empty($new_value_comparable)) {
                        $new_user_data = get_userdata($new_value_comparable);
                        $new_user_display = $new_user_data ? $new_user_data->display_name : sprintf(__('Unknown User (ID: %s)', 'asset-manager-mvc'), $new_value_comparable);
                    }
                    $changes[] = sprintf(esc_html__('%1$s changed from "%2$s" to "%3$s"', 'asset-manager-mvc'), esc_html($label), esc_html($old_user_display), esc_html($new_user_display));
                } else {
                     $changes[] = sprintf(esc_html__('%1$s changed from "%2$s" to "%3$s"', 'asset-manager-mvc'), esc_html($label), esc_html((string)$old_value), esc_html((string)$new_value_sanitized));
                }
            }
        }

        // Handle Category
        $category_post_key = ASSET_MANAGER_MVC_META_PREFIX . 'asset_category';
        if (isset($data[$category_post_key])) {
            $new_term_id = absint($data[$category_post_key]);
            $old_terms = wp_get_post_terms($post_id, ASSET_MANAGER_MVC_TAXONOMY, ['fields' => 'ids']);
            $old_term_id = !empty($old_terms) && isset($old_terms[0]) ? absint($old_terms[0]) : 0;

            if ($new_term_id !== $old_term_id) {
                 wp_set_post_terms($post_id, ($new_term_id ? [$new_term_id] : []), ASSET_MANAGER_MVC_TAXONOMY, false);
                 $old_term_obj = $old_term_id ? get_term($old_term_id, ASSET_MANAGER_MVC_TAXONOMY) : null;
                 $new_term_obj = $new_term_id ? get_term($new_term_id, ASSET_MANAGER_MVC_TAXONOMY) : null;
                 $old_term_name = ($old_term_obj && !is_wp_error($old_term_obj)) ? $old_term_obj->name : __('None', 'asset-manager-mvc');
                 $new_term_name = ($new_term_obj && !is_wp_error($new_term_obj)) ? $new_term_obj->name : __('None', 'asset-manager-mvc');
                 $changes[] = sprintf(esc_html__('Category changed from "%1$s" to "%2$s"', 'asset-manager-mvc'), esc_html($old_term_name), esc_html($new_term_name));
            }
        }

        if (!empty($changes)) {
            $history_entry = ['date' => current_time('mysql'), 'user' => get_current_user_id(), 'note' => implode('; ', $changes)];
            $current_history[] = $history_entry;
            update_post_meta($post_id, ASSET_MANAGER_MVC_META_PREFIX . 'history', $current_history);
        }
        return $changes;
    }

    /**
     * Retrieves asset history.
     * @param int $post_id The ID of the asset post.
     * @return array Asset history entries.
     */
    public function get_asset_history($post_id) {
        $history = get_post_meta($post_id, ASSET_MANAGER_MVC_META_PREFIX . 'history', true);
        return (empty($history) || !is_array($history)) ? [] : array_reverse($history);
    }


    /**
     * Retrieves data for the dashboard charts.
     * @return array Data for status, user, and category charts.
     */
    public function get_dashboard_data() {
        $status_data = [];
        $user_data = [];
        $category_data_counts = [];

        // Initialize status data
        foreach ($this->status_options as $status_opt) {
            $status_data[$status_opt] = 0;
        }
        $status_data[__('Unknown', 'asset-manager-mvc')] = 0;

        // Initialize category data
        $all_categories = get_terms(['taxonomy' => ASSET_MANAGER_MVC_TAXONOMY, 'hide_empty' => false]);
        if (is_array($all_categories)) {
            foreach ($all_categories as $cat_term) {
                if (is_object($cat_term) && property_exists($cat_term, 'name')) {
                    $category_data_counts[esc_html($cat_term->name)] = 0;
                }
            }
        }
        $category_data_counts[__('Uncategorized', 'asset-manager-mvc')] = 0;
        $user_data[__('Unassigned', 'asset-manager-mvc')] = 0;

        $assets_query = new \\WP_Query([
            'post_type' => ASSET_MANAGER_MVC_POST_TYPE,
            'posts_per_page' => -1,
        ]);

        if ($assets_query->have_posts()) {
            while ($assets_query->have_posts()) {
                $assets_query->the_post();
                $post_id = get_the_ID();

                // Status
                $status_val = get_post_meta($post_id, ASSET_MANAGER_MVC_META_PREFIX . 'status', true);
                $display_status = '';
                if (empty($status_val)) {
                    $display_status = 'Unassigned';
                } elseif (in_array($status_val, $this->status_options, true)) {
                    $display_status = $status_val;
                } else {
                    $display_status = __('Unknown', 'asset-manager-mvc');
                }
                if (!isset($status_data[$display_status])) $status_data[$display_status] = 0;
                $status_data[$display_status]++;

                // User
                $user_id = get_post_meta($post_id, ASSET_MANAGER_MVC_META_PREFIX . 'issued_to', true);
                $user_name_key = __('Unassigned', 'asset-manager-mvc');
                if ($user_id) {
                    $user = get_userdata($user_id);
                    $user_name_key = $user ? esc_html($user->display_name) : sprintf(__('Unknown User (ID: %d)', 'asset-manager-mvc'), $user_id);
                }
                if (!isset($user_data[$user_name_key])) $user_data[$user_name_key] = 0;
                $user_data[$user_name_key]++;

                // Category
                $terms = get_the_terms($post_id, ASSET_MANAGER_MVC_TAXONOMY);
                $category_name_key = __('Uncategorized', 'asset-manager-mvc');
                if (!empty($terms) && !is_wp_error($terms) && isset($terms[0]->name)) {
                     $category_name_key = esc_html($terms[0]->name);
                }
                if (!isset($category_data_counts[$category_name_key])) $category_data_counts[$category_name_key] = 0;
                $category_data_counts[$category_name_key]++;
            }
            wp_reset_postdata();
        }
        return [
            'status' => array_filter($status_data, function($count){ return $count >= 0; }),
            'users' => array_filter($user_data, function($count){ return $count > 0; }),
            'categories' => array_filter($category_data_counts, function($count){ return $count > 0; })
        ];
    }

    /**
     * Get all assets for PDF export.
     * @return \\WP_Query
     */
    public function get_all_assets_for_export() {
        return new \\WP_Query([
            'post_type' => ASSET_MANAGER_MVC_POST_TYPE,
            'posts_per_page' => -1,
            'orderby' => 'title',
            'order' => 'ASC'
        ]);
    }
}
"""

# Setup Controller: includes/controllers/class-setup-controller.php
setup_controller_php_content = """<?php
// File: includes/controllers/class-setup-controller.php

namespace AssetManagerMvc\\Controllers;

if (!defined('ABSPATH')) exit;

/**
 * Setup_Controller Class
 *
 * Handles plugin setup tasks like CPT and taxonomy registration.
 */
class Setup_Controller {

    /**
     * Registers WordPress hooks.
     */
    public function register_hooks() {
        add_action('init', [$this, 'register_asset_post_type']);
        add_action('init', [$this, 'register_asset_taxonomy']);
        // add_action('init', [$this, 'register_shortcodes']); // Placeholder
    }

    /**
     * Plugin activation tasks.
     */
    public function activate() {
        // Ensure CPT and taxonomy are registered before flushing rewrite rules
        $this->register_asset_post_type();
        $this->register_asset_taxonomy();
        // flush_rewrite_rules(); // Done in main plugin file's activation hook
    }

    /**
     * Registers the 'asset_mvc' custom post type.
     */
    public function register_asset_post_type() {
        $labels = [
            'name' => _x('Assets (MVC)', 'post type general name', 'asset-manager-mvc'),
            'singular_name' => _x('Asset (MVC)', 'post type singular name', 'asset-manager-mvc'),
            'menu_name' => _x('Assets (MVC)', 'admin menu', 'asset-manager-mvc'),
            'name_admin_bar' => _x('Asset (MVC)', 'add new on admin bar', 'asset-manager-mvc'),
            'add_new' => _x('Add New', 'asset', 'asset-manager-mvc'),
            'add_new_item' => __('Add New Asset', 'asset-manager-mvc'),
            'new_item' => __('New Asset', 'asset-manager-mvc'),
            'edit_item' => __('Edit Asset', 'asset-manager-mvc'),
            'view_item' => __('View Asset', 'asset-manager-mvc'),
            'all_items' => __('All Assets', 'asset-manager-mvc'),
            'search_items' => __('Search Assets', 'asset-manager-mvc'),
            'parent_item_colon' => __('Parent Assets:', 'asset-manager-mvc'),
            'not_found' => __('No assets found.', 'asset-manager-mvc'),
            'not_found_in_trash' => __('No assets found in Trash.', 'asset-manager-mvc'),
            'attributes' => __( 'Asset Attributes', 'asset-manager-mvc' ),
        ];
        $args = [
            'labels' => $labels,
            'public' => false, // Typically false for internal management CPTs
            'show_ui' => true,
            'show_in_menu' => true,
            'query_var' => true,
            'rewrite' => ['slug' => ASSET_MANAGER_MVC_POST_TYPE],
            'capability_type' => 'post',
            'has_archive' => false,
            'hierarchical' => false,
            'menu_position' => 20,
            'supports' => ['title'], // Custom fields will handle other data
            'menu_icon' => 'dashicons-archive',
            'show_in_rest' => true, // For Gutenberg / Block Editor compatibility
        ];
        register_post_type(ASSET_MANAGER_MVC_POST_TYPE, $args);
    }

    /**
     * Registers the 'asset_category_mvc' custom taxonomy.
     */
    public function register_asset_taxonomy() {
        $labels = [
            'name' => _x('Asset Categories (MVC)', 'taxonomy general name', 'asset-manager-mvc'),
            'singular_name' => _x('Asset Category (MVC)', 'taxonomy singular name', 'asset-manager-mvc'),
            'search_items' => __('Search Asset Categories', 'asset-manager-mvc'),
            'all_items' => __('All Asset Categories', 'asset-manager-mvc'),
            'parent_item' => __('Parent Asset Category', 'asset-manager-mvc'),
            'parent_item_colon' => __('Parent Asset Category:', 'asset-manager-mvc'),
            'edit_item' => __('Edit Asset Category', 'asset-manager-mvc'),
            'update_item' => __('Update Asset Category', 'asset-manager-mvc'),
            'add_new_item' => __('Add New Asset Category', 'asset-manager-mvc'),
            'new_item_name' => __('New Asset Category Name', 'asset-manager-mvc'),
            'menu_name' => __('Categories', 'asset-manager-mvc'),
        ];
        $args = [
            'hierarchical' => true,
            'labels' => $labels,
            'show_ui' => true,
            'show_admin_column' => true,
            'query_var' => true,
            'rewrite' => ['slug' => ASSET_MANAGER_MVC_TAXONOMY],
            'show_in_rest' => true,
        ];
        register_taxonomy(ASSET_MANAGER_MVC_TAXONOMY, ASSET_MANAGER_MVC_POST_TYPE, $args);
    }

    // public function register_shortcodes() { /* Placeholder for future shortcodes */ }
}
"""

# Asset Controller: includes/controllers/class-asset-controller.php
asset_controller_php_content = """<?php
// File: includes/controllers/class-asset-controller.php

namespace AssetManagerMvc\\Controllers;

use AssetManagerMvc\\Models\\Asset_Model;

if (!defined('ABSPATH')) exit;

/**
 * Asset_Controller Class
 *
 * Handles asset creation, editing, display, and admin list customizations.
 */
class Asset_Controller {

    /**
     * Asset Model instance.
     * @var Asset_Model
     */
    private $asset_model;

    /**
     * Constructor.
     * @param Asset_Model $asset_model Instance of the Asset Model.
     */
    public function __construct(Asset_Model $asset_model) {
        $this->asset_model = $asset_model;
    }

    /**
     * Registers WordPress hooks.
     */
    public function register_hooks() {
        add_action('add_meta_boxes', [$this, 'register_meta_boxes']);
        add_action('save_post_' . ASSET_MANAGER_MVC_POST_TYPE, [$this, 'handle_save_asset'], 10, 2);
        
        add_filter('manage_' . ASSET_MANAGER_MVC_POST_TYPE . '_posts_columns', [$this, 'customize_admin_columns']);
        add_action('manage_' . ASSET_MANAGER_MVC_POST_TYPE . '_posts_custom_column', [$this, 'render_custom_column_content'], 10, 2);
        
        add_action('admin_enqueue_scripts', [$this, 'enqueue_admin_assets']);
        add_action('admin_notices', [$this, 'display_admin_notices']);
    }

    /**
     * Enqueues admin scripts and styles.
     */
    public function enqueue_admin_assets($hook) {
        global $post_type, $pagenow;

        $is_asset_cpt_screen = ($post_type === ASSET_MANAGER_MVC_POST_TYPE && in_array($pagenow, ['post.php', 'post-new.php']));

        if ($is_asset_cpt_screen) {
            wp_enqueue_style(
                'asset-manager-mvc-admin-css',
                ASSET_MANAGER_MVC_URL . 'assets/css/asset-manager-admin.css',
                [],
                ASSET_MANAGER_MVC_VERSION
            );
            wp_enqueue_script(
                'asset-manager-mvc-admin-js',
                ASSET_MANAGER_MVC_URL . 'assets/js/asset-manager-admin.js',
                ['jquery'],
                ASSET_MANAGER_MVC_VERSION,
                true
            );
             // Add this to your asset-manager-admin.css:
             // .asset-fields .required { color: red; margin-left: 2px; }
        }
    }

    /**
     * Registers meta boxes for the asset post type.
     */
    public function register_meta_boxes() {
        add_meta_box(
            ASSET_MANAGER_MVC_META_PREFIX . 'details',
            __('Asset Details', 'asset-manager-mvc'),
            [$this, 'render_asset_fields_meta_box_view'],
            ASSET_MANAGER_MVC_POST_TYPE,
            'normal',
            'high'
        );
        add_meta_box(
            ASSET_MANAGER_MVC_META_PREFIX . 'history',
            __('Asset History', 'asset-manager-mvc'),
            [$this, 'render_history_meta_box_view'],
            ASSET_MANAGER_MVC_POST_TYPE,
            'normal',
            'default'
        );
    }

    /**
     * Renders the asset fields meta box by loading the view.
     * @param \\WP_Post $post The current post object.
     */
    public function render_asset_fields_meta_box_view($post) {
        wp_nonce_field(ASSET_MANAGER_MVC_META_PREFIX . 'save_details_nonce', ASSET_MANAGER_MVC_META_PREFIX . 'details_nonce');
        
        $data['meta_values'] = $this->asset_model->get_asset_meta($post->ID);
        $data['users'] = get_users(['orderby' => 'display_name']);
        $data['categories'] = get_terms(['taxonomy' => ASSET_MANAGER_MVC_TAXONOMY, 'hide_empty' => false]);
        $data['field_definitions'] = $this->asset_model->get_fields(); // e.g. ['asset_tag', 'model', ...]
        $data['field_labels'] = $this->asset_model->get_field_labels();
        $data['status_options'] = $this->asset_model->get_status_options();
        $data['meta_prefix'] = ASSET_MANAGER_MVC_META_PREFIX;
        $data['taxonomy_slug'] = ASSET_MANAGER_MVC_TAXONOMY;

        // Load the view
        $this->load_view('admin/asset-fields-meta-box', $data);
    }

    /**
     * Renders the asset history meta box by loading the view.
     * @param \\WP_Post $post The current post object.
     */
    public function render_history_meta_box_view($post) {
        $data['history_entries'] = $this->asset_model->get_asset_history($post->ID);
        $this->load_view('admin/asset-history-meta-box', $data);
    }

    /**
     * Handles saving asset meta data.
     * @param int $post_id The ID of the post being saved.
     * @param \\WP_Post $post The post object.
     */
    public function handle_save_asset($post_id, $post) {
        // Verify nonce
        if (!isset($_POST[ASSET_MANAGER_MVC_META_PREFIX . 'details_nonce']) || !wp_verify_nonce($_POST[ASSET_MANAGER_MVC_META_PREFIX . 'details_nonce'], ASSET_MANAGER_MVC_META_PREFIX . 'save_details_nonce')) {
            return;
        }
        // Check user permissions
        if (!current_user_can('edit_post', $post_id)) {
            return;
        }
        // Ignore autosaves
        if (defined('DOING_AUTOSAVE') && DOING_AUTOSAVE) {
            return;
        }
        // Ensure it's our CPT
        if ($post->post_type !== ASSET_MANAGER_MVC_POST_TYPE) {
            return;
        }

        $errors = $this->asset_model->validate_asset_data($_POST);
        
        if (!empty($errors)) {
            // Store errors in a transient to display after redirect
            set_transient('asset_manager_errors_' . $post_id . '_' . get_current_user_id(), $errors, 45);
            // Prevent WordPress from showing its default "Post updated" message
            add_filter('redirect_post_location', function($location) use ($post_id) {
                if (get_transient('asset_manager_errors_' . $post_id . '_' . get_current_user_id())) {
                    // Remove the 'message' query arg from the redirect URL
                    return remove_query_arg('message', $location);
                }
                return $location;
            }, 99); // High priority to run late
            return; // Stop further processing
        }

        // Save data using the model
        $this->asset_model->save_asset_data($post_id, $_POST);

        // Update post title if it's empty or default, based on asset tag
        $post_obj = get_post($post_id);
        if ($post_obj && (empty($post_obj->post_title) || $post_obj->post_title === __('Auto Draft') || $post_obj->post_title === '')) {
            $asset_tag_val = get_post_meta($post_id, ASSET_MANAGER_MVC_META_PREFIX . 'asset_tag', true);
            $new_title = !empty($asset_tag_val) ? sprintf(__('Asset: %s', 'asset-manager-mvc'), $asset_tag_val) : sprintf(__('Asset #%d', 'asset-manager-mvc'), $post_id);
            
            // Temporarily remove this action to prevent recursion
            remove_action('save_post_' . ASSET_MANAGER_MVC_POST_TYPE, [$this, 'handle_save_asset'], 10);
            wp_update_post(['ID' => $post_id, 'post_title' => $new_title]);
            // Re-add the action
            add_action('save_post_' . ASSET_MANAGER_MVC_POST_TYPE, [$this, 'handle_save_asset'], 10, 2);
        }
    }

    /**
     * Displays admin notices for validation errors.
     */
    public function display_admin_notices() {
        global $pagenow, $post;
        if (($pagenow == 'post.php' || $pagenow == 'post-new.php') && isset($post->post_type) && $post->post_type == ASSET_MANAGER_MVC_POST_TYPE) {
            $transient_key = 'asset_manager_errors_' . $post->ID . '_' . get_current_user_id();
            $errors = get_transient($transient_key);

            if (!empty($errors) && is_array($errors)) {
                $data['errors'] = $errors;
                $this->load_view('admin/notices/validation-errors', $data);
                delete_transient($transient_key); // Clear after displaying
            }
        }
    }

    /**
     * Customizes the columns in the admin list table for assets.
     * @param array $columns Existing columns.
     * @return array Modified columns.
     */
    public function customize_admin_columns($columns) {
        // cb, title, date are standard
        $new_columns = [
            'cb' => $columns['cb'],
            'title' => __('Title', 'asset-manager-mvc'),
            'asset_tag' => __('Asset Tag', 'asset-manager-mvc'),
            'model' => __('Model', 'asset-manager-mvc'),
            'serial_number' => __('Serial Number', 'asset-manager-mvc'),
            'brand' => __('Brand', 'asset-manager-mvc'),
            ASSET_MANAGER_MVC_TAXONOMY => __('Category', 'asset-manager-mvc'), // Use taxonomy slug
            'status' => __('Status', 'asset-manager-mvc'),
            'issued_to' => __('Issued To', 'asset-manager-mvc'),
            'date' => __('Date', 'asset-manager-mvc')
        ];
        return $new_columns;
    }

    /**
     * Renders content for custom columns in the admin list table.
     * @param string $column The name of the column.
     * @param int $post_id The ID of the current post.
     */
    public function render_custom_column_content($column, $post_id) {
        switch ($column) {
            case 'asset_tag':
                echo esc_html(get_post_meta($post_id, ASSET_MANAGER_MVC_META_PREFIX . 'asset_tag', true));
                break;
            case 'model':
                echo esc_html(get_post_meta($post_id, ASSET_MANAGER_MVC_META_PREFIX . 'model', true));
                break;
            case 'serial_number':
                echo esc_html(get_post_meta($post_id, ASSET_MANAGER_MVC_META_PREFIX . 'serial_number', true));
                break;
            case 'brand':
                echo esc_html(get_post_meta($post_id, ASSET_MANAGER_MVC_META_PREFIX . 'brand', true));
                break;
            case ASSET_MANAGER_MVC_TAXONOMY: // Use taxonomy slug
                $terms = get_the_terms($post_id, ASSET_MANAGER_MVC_TAXONOMY);
                if (!empty($terms) && !is_wp_error($terms)) {
                    echo esc_html(implode(', ', wp_list_pluck($terms, 'name')));
                } else {
                    echo '—';
                }
                break;
            case 'status':
                echo esc_html(get_post_meta($post_id, ASSET_MANAGER_MVC_META_PREFIX . 'status', true));
                break;
            case 'issued_to':
                $user_id = get_post_meta($post_id, ASSET_MANAGER_MVC_META_PREFIX . 'issued_to', true);
                if ($user_id) {
                    $user = get_userdata($user_id);
                    echo esc_html($user ? $user->display_name : __('Unknown User', 'asset-manager-mvc'));
                } else {
                    echo '—';
                }
                break;
        }
    }

    /**
     * Helper function to load a view file.
     * @param string $view_name The name of the view file (without .php).
     * @param array $data Data to pass to the view.
     */
    protected function load_view($view_name, $data = []) {
        // Make data available to the view file
        extract($data);
        $file_path = ASSET_MANAGER_MVC_PATH . 'includes/views/' . $view_name . '.php';
        if (file_exists($file_path)) {
            include $file_path;
        } else {
            // Optionally, log an error or display a message if the view file is not found
            echo "<p>Error: View file not found at {$file_path}</p>";
        }
    }
}
"""

# Dashboard Controller: includes/controllers/class-dashboard-controller.php
dashboard_controller_php_content = """<?php
// File: includes/controllers/class-dashboard-controller.php

namespace AssetManagerMvc\\Controllers;

use AssetManagerMvc\\Models\\Asset_Model;

if (!defined('ABSPATH')) exit;

/**
 * Dashboard_Controller Class
 *
 * Handles the display of the asset dashboard.
 */
class Dashboard_Controller {

    private $asset_model;

    public function __construct(Asset_Model $asset_model) {
        $this->asset_model = $asset_model;
    }

    public function register_hooks() {
        add_action('admin_menu', [$this, 'register_dashboard_page']);
        add_action('admin_enqueue_scripts', [$this, 'enqueue_dashboard_assets']);
    }

    public function register_dashboard_page() {
        add_submenu_page(
            'edit.php?post_type=' . ASSET_MANAGER_MVC_POST_TYPE,
            __('Asset Dashboard', 'asset-manager-mvc'),
            __('Dashboard', 'asset-manager-mvc'),
            'manage_options', // Capability
            'asset_mvc_dashboard', // Menu slug
            [$this, 'render_dashboard_page_view']
        );
    }

    public function enqueue_dashboard_assets($hook) {
        // Check if we are on the dashboard page
        $current_screen = get_current_screen();
        if ($current_screen && $current_screen->id === ASSET_MANAGER_MVC_POST_TYPE . '_page_asset_mvc_dashboard') {
             wp_enqueue_style(
                'asset-manager-mvc-admin-css', // Can reuse if styles are general
                ASSET_MANAGER_MVC_URL . 'assets/css/asset-manager-admin.css',
                [],
                ASSET_MANAGER_MVC_VERSION
            );
            wp_enqueue_script('chart-js', 'https://cdn.jsdelivr.net/npm/chart.js', [], '4.4.1', true);
            wp_enqueue_script(
                'asset-dashboard-mvc-js',
                ASSET_MANAGER_MVC_URL . 'assets/js/asset-dashboard.js', // Assuming you have this JS file
                ['jquery', 'chart-js'],
                ASSET_MANAGER_MVC_VERSION,
                true
            );

            // Localize script with data for charts
            wp_localize_script('asset-dashboard-mvc-js', 'assetDashboardData', $this->asset_model->get_dashboard_data());
        }
    }

    public function render_dashboard_page_view() {
        // Data for the view is already localized for JS.
        $this->load_view('admin/dashboard-page');
    }

    protected function load_view($view_name, $data = []) {
        extract($data);
        $file_path = ASSET_MANAGER_MVC_PATH . 'includes/views/' . $view_name . '.php';
        if (file_exists($file_path)) {
            include $file_path;
        } else {
            echo "<p>Error: View file not found at {$file_path}</p>";
        }
    }
}
"""

# Export Controller: includes/controllers/class-export-controller.php
export_controller_php_content = """<?php
// File: includes/controllers/class-export-controller.php

namespace AssetManagerMvc\\Controllers;

use AssetManagerMvc\\Models\\Asset_Model;

if (!defined('ABSPATH')) exit;

/**
 * Export_Controller Class
 *
 * Handles asset exporting functionality, e.g., to PDF.
 */
class Export_Controller {

    private $asset_model;

    public function __construct(Asset_Model $asset_model) {
        $this->asset_model = $asset_model;
    }

    public function register_hooks() {
        add_action('admin_menu', [$this, 'register_export_page']);
        add_action('admin_post_am_mvc_export_assets_pdf_action', [$this, 'handle_pdf_export']);
    }

    public function register_export_page() {
        add_submenu_page(
            'edit.php?post_type=' . ASSET_MANAGER_MVC_POST_TYPE,
            __('Export Assets', 'asset-manager-mvc'),
            __('Export to PDF', 'asset-manager-mvc'),
            'manage_options',
            'export_assets_mvc', // Menu slug
            [$this, 'render_export_page_view']
        );
    }

    public function render_export_page_view() {
        $this->load_view('admin/export-page');
    }

    public function handle_pdf_export() {
        if (!isset($_POST['am_mvc_export_nonce']) || !wp_verify_nonce($_POST['am_mvc_export_nonce'], 'am_mvc_export_assets_pdf_nonce')) {
            wp_die(__('Security check failed.', 'asset-manager-mvc'), __('Error', 'asset-manager-mvc'), ['response' => 403]);
        }
        if (!current_user_can('manage_options')) {
            wp_die(__('You do not have sufficient permissions to export assets.', 'asset-manager-mvc'), __('Error', 'asset-manager-mvc'), ['response' => 403]);
        }

        // Ensure mPDF is available (assuming it's in vendor directory)
        $mpdf_autoloader = ASSET_MANAGER_MVC_PATH . 'vendor/autoload.php';
        if (file_exists($mpdf_autoloader) && !class_exists('\\Mpdf\\Mpdf')) {
            require_once $mpdf_autoloader;
        }
        if (!class_exists('\\Mpdf\\Mpdf')) {
            wp_die(
                __('PDF Export library (mPDF) is missing or could not be loaded. Please ensure it is installed in the plugin\\'s vendor directory.', 'asset-manager-mvc'),
                __('PDF Library Error', 'asset-manager-mvc'),
                ['back_link' => true]
            );
            return;
        }

        $assets_query = $this->asset_model->get_all_assets_for_export();
        
        // Prepare data for the PDF template view
        $data_for_pdf_view = [
            'assets_query' => $assets_query,
            'asset_model' => $this->asset_model, // Pass model for field definitions if needed
            'meta_prefix' => ASSET_MANAGER_MVC_META_PREFIX,
            'taxonomy_slug' => ASSET_MANAGER_MVC_TAXONOMY
        ];

        // Get HTML content from a view file
        ob_start();
        $this->load_view('pdf/asset-export-template', $data_for_pdf_view);
        $html = ob_get_clean();
        
        try {
            $mpdf = new \\Mpdf\\Mpdf(['mode' => 'utf-8', 'format' => 'A4-L']);
            $mpdf->SetTitle(esc_attr__('Asset List', 'asset-manager-mvc'));
            $mpdf->SetAuthor(esc_attr(get_bloginfo('name')));
            $mpdf->WriteHTML($html);
            $mpdf->Output('assets-mvc-' . date('Y-m-d') . '.pdf', 'D'); // D for download
            exit;
        } catch (\\Mpdf\\MpdfException $e) {
            wp_die(
                sprintf(esc_html__('Error generating PDF: %s', 'asset-manager-mvc'), esc_html($e->getMessage())),
                esc_html__('PDF Generation Error', 'asset-manager-mvc'),
                ['back_link' => true]
            );
        }
    }

    protected function load_view($view_name, $data = []) {
        extract($data);
        $file_path = ASSET_MANAGER_MVC_PATH . 'includes/views/' . $view_name . '.php';
        if (file_exists($file_path)) {
            include $file_path;
        } else {
             echo "<p>Error: View file not found at {$file_path}</p>";
        }
    }
}
"""

# View: includes/views/admin/asset-fields-meta-box.php
view_asset_fields_php_content = """<?php
// File: includes/views/admin/asset-fields-meta-box.php
/**
 * Variables available:
 * @var array $meta_values Current meta values for the post.
 * @var array $users List of WP_User objects.
 * @var array $categories List of term objects for asset categories.
 * @var array $field_definitions Array of field keys (e.g., 'asset_tag', 'model').
 * @var array $field_labels Associative array of field_key => Label Text.
 * @var array $status_options Array of status strings.
 * @var string $meta_prefix The meta prefix for field names.
 * @var string $taxonomy_slug The slug for the asset category taxonomy.
 * @var \\WP_Post $post The current post object (implicitly available in meta box callbacks).
 */

if (!defined('ABSPATH')) exit;
?>
<div class="asset-fields">
    <?php foreach ($field_definitions as $field_key) :
        $field_id = 'am_mvc_' . str_replace('_', '-', $field_key); // e.g., am_mvc_asset-tag
        $field_name_attr = $meta_prefix . $field_key; // e.g., _asset_manager_mvc_asset_tag
        $label_text = isset($field_labels[$field_key]) ? $field_labels[$field_key] : ucfirst(str_replace('_', ' ', $field_key));
        $current_value = isset($meta_values[$field_key]) ? $meta_values[$field_key] : '';
    ?>
    <p>
        <label for="<?php echo esc_attr($field_id); ?>"><?php echo esc_html($label_text); ?>: <span class="required">*</span></label>
        <?php if ($field_key === 'issued_to') : ?>
            <select id="<?php echo esc_attr($field_id); ?>" name="<?php echo esc_attr($field_name_attr); ?>" class="widefat" required>
                <option value=""><?php esc_html_e('-- Select User --', 'asset-manager-mvc'); ?></option>
                <?php foreach ($users as $user): ?>
                    <option value="<?php echo esc_attr($user->ID); ?>" <?php selected($current_value, $user->ID); ?>>
                        <?php echo esc_html($user->display_name . ' (' . $user->user_email . ')'); ?>
                    </option>
                <?php endforeach; ?>
            </select>
        <?php elseif ($field_key === 'status') : ?>
            <select id="<?php echo esc_attr($field_id); ?>" name="<?php echo esc_attr($field_name_attr); ?>" class="widefat" required>
                <option value=""><?php esc_html_e('-- Select Status --', 'asset-manager-mvc'); ?></option>
                <?php foreach ($status_options as $status_option) : ?>
                    <option value="<?php echo esc_attr($status_option); ?>" <?php selected($current_value, $status_option); ?>>
                        <?php echo esc_html__($status_option, 'asset-manager-mvc'); // Allow translation of statuses ?>
                    </option>
                <?php endforeach; ?>
            </select>
        <?php elseif ($field_key === 'description') : ?>
            <textarea id="<?php echo esc_attr($field_id); ?>" name="<?php echo esc_attr($field_name_attr); ?>" class="widefat" rows="5" required><?php echo esc_textarea($current_value); ?></textarea>
        <?php elseif ($field_key === 'date_purchased') : ?>
            <input type="date" id="<?php echo esc_attr($field_id); ?>" name="<?php echo esc_attr($field_name_attr); ?>" value="<?php echo esc_attr($current_value); ?>" class="widefat" required>
        <?php else : // For asset_tag, serial_number, brand, model, supplier ?>
            <input type="text" id="<?php echo esc_attr($field_id); ?>" name="<?php echo esc_attr($field_name_attr); ?>" value="<?php echo esc_attr($current_value); ?>" class="widefat" required>
        <?php endif; ?>
    </p>
    <?php endforeach; ?>

    <p>
        <label for="am_mvc_asset_category"><?php esc_html_e('Category:', 'asset-manager-mvc'); ?> <span class="required">*</span></label>
        <select id="am_mvc_asset_category" name="<?php echo esc_attr($meta_prefix . 'asset_category'); ?>" class="widefat" required>
            <option value=""><?php esc_html_e('-- Select Category --', 'asset-manager-mvc'); ?></option>
            <?php foreach ($categories as $cat): ?>
                <option value="<?php echo esc_attr($cat->term_id); ?>" <?php selected(has_term($cat->term_id, $taxonomy_slug, $post->ID)); ?>>
                    <?php echo esc_html($cat->name); ?>
                </option>
            <?php endforeach; ?>
        </select>
    </p>
</div>
<?php // Note: The class .required { color: red; margin-left: 2px; } should be in your admin CSS file. ?>
"""

# View: includes/views/admin/asset-history-meta-box.php
view_asset_history_php_content = """<?php
// File: includes/views/admin/asset-history-meta-box.php
/**
 * Variables available:
 * @var array $history_entries Array of history log entries.
 */

if (!defined('ABSPATH')) exit;

if (empty($history_entries)) {
    echo '<p>' . esc_html__('No history available.', 'asset-manager-mvc') . '</p>';
    return;
}
?>
<ul class="asset-history">
    <?php foreach ($history_entries as $entry) :
        $user_info = '';
        if (!empty($entry['user'])) {
            $user_data = get_userdata($entry['user']);
            if ($user_data) {
                $user_info = ' (' . esc_html($user_data->display_name) . ')';
            }
        }
        $formatted_date = !empty($entry['date']) ? mysql2date(get_option('date_format') . ' @ ' . get_option('time_format'), $entry['date']) : __('Unknown Date', 'asset-manager-mvc');
    ?>
    <li>
        <strong><?php echo esc_html($formatted_date) . esc_html($user_info); ?>:</strong>
        <?php echo wp_kses_post($entry['note']); // Use wp_kses_post for notes that might contain some HTML ?>
    </li>
    <?php endforeach; ?>
</ul>
"""

# View: includes/views/admin/notices/validation-errors.php
view_validation_errors_php_content = """<?php
// File: includes/views/admin/notices/validation-errors.php
/**
 * Variables available:
 * @var array $errors Array of error messages.
 */
if (!defined('ABSPATH')) exit;

if (empty($errors) || !is_array($errors)) {
    return;
}
?>
<div id="message" class="notice notice-error is-dismissible">
    <p><strong><?php esc_html_e('Please correct the following errors:', 'asset-manager-mvc'); ?></strong></p>
    <ul>
        <?php foreach ($errors as $error) : ?>
            <li><?php echo esc_html($error); ?></li>
        <?php endforeach; ?>
    </ul>
</div>
"""

# View: includes/views/admin/dashboard-page.php
view_dashboard_page_php_content = """<?php
// File: includes/views/admin/dashboard-page.php
/**
 * Data for charts is expected to be localized to asset-dashboard-mvc-js via wp_localize_script.
 * The JS file (assets/js/asset-dashboard.js) will handle chart rendering.
 */
if (!defined('ABSPATH')) exit;
?>
<div class="wrap asset-manager-dashboard">
    <h1><?php esc_html_e('Asset Dashboard', 'asset-manager-mvc'); ?></h1>
    <div class="dashboard-widgets-wrapper">
        <div class="dashboard-widget">
            <h2><?php esc_html_e('Assets by Status', 'asset-manager-mvc'); ?></h2>
            <div class="chart-container"><canvas id="assetMvcStatusChart"></canvas></div>
        </div>
        <div class="dashboard-widget">
            <h2><?php esc_html_e('Assets by User', 'asset-manager-mvc'); ?></h2>
            <div class="chart-container"><canvas id="assetMvcUserChart"></canvas></div>
        </div>
        <div class="dashboard-widget">
            <h2><?php esc_html_e('Assets by Category', 'asset-manager-mvc'); ?></h2>
            <div class="chart-container"><canvas id="assetMvcCategoryChart"></canvas></div>
        </div>
    </div>
</div>
<?php // Ensure your asset-dashboard.js targets these canvas IDs: assetMvcStatusChart, assetMvcUserChart, assetMvcCategoryChart ?>
"""

# View: includes/views/admin/export-page.php
view_export_page_php_content = """<?php
// File: includes/views/admin/export-page.php
if (!defined('ABSPATH')) exit;
?>
<div class="wrap">
    <h1><?php esc_html_e('Export Assets to PDF', 'asset-manager-mvc'); ?></h1>
    <form method="post" action="<?php echo esc_url(admin_url('admin-post.php')); ?>">
        <input type="hidden" name="action" value="am_mvc_export_assets_pdf_action">
        <?php wp_nonce_field('am_mvc_export_assets_pdf_nonce', 'am_mvc_export_nonce'); ?>
        <?php submit_button(__('Export All Assets as PDF', 'asset-manager-mvc')); ?>
    </form>
</div>
"""

# View: includes/views/pdf/asset-export-template.php
view_pdf_template_php_content = """<?php
// File: includes/views/pdf/asset-export-template.php
/**
 * Variables available:
 * @var \\WP_Query $assets_query The query object for assets.
 * @var \\AssetManagerMvc\\Models\\Asset_Model $asset_model Instance of Asset_Model.
 * @var string $meta_prefix The meta prefix.
 * @var string $taxonomy_slug The taxonomy slug.
 */
if (!defined('ABSPATH')) exit; // Should not be accessed directly, but good practice.

// This file generates HTML that will be converted to PDF by mPDF.
// Basic styling is included here. More complex styling can be added.
?>
<style>
    body { font-family: sans-serif; font-size: 10px; }
    table { width: 100%; border-collapse: collapse; margin-bottom: 20px; }
    th, td { border: 1px solid #ddd; padding: 6px; text-align: left; vertical-align: top; word-wrap: break-word; }
    th { background-color: #f2f2f2; font-weight: bold; }
    h1 { text-align: center; margin-bottom: 20px; font-size: 16px; }
    .no-assets { text-align: center; font-style: italic; }
</style>

<h1><?php esc_html_e('Asset List', 'asset-manager-mvc'); ?></h1>

<table>
    <thead>
        <tr>
            <th><?php esc_html_e('Title', 'asset-manager-mvc'); ?></th>
            <th><?php esc_html_e('Asset Tag', 'asset-manager-mvc'); ?></th>
            <th><?php esc_html_e('Model', 'asset-manager-mvc'); ?></th>
            <th><?php esc_html_e('Serial No.', 'asset-manager-mvc'); ?></th>
            <th><?php esc_html_e('Brand', 'asset-manager-mvc'); ?></th>
            <th><?php esc_html_e('Category', 'asset-manager-mvc'); ?></th>
            <th><?php esc_html_e('Status', 'asset-manager-mvc'); ?></th>
            <th><?php esc_html_e('Issued To', 'asset-manager-mvc'); ?></th>
            <th><?php esc_html_e('Date Purchased', 'asset-manager-mvc'); ?></th>
            <th><?php esc_html_e('Description', 'asset-manager-mvc'); ?></th>
        </tr>
    </thead>
    <tbody>
        <?php if ($assets_query->have_posts()) : ?>
            <?php while ($assets_query->have_posts()) : $assets_query->the_post(); ?>
                <?php
                $post_id = get_the_ID();
                $meta = $asset_model->get_asset_meta($post_id); // Get all meta using model method
                $issued_to_name = '—';
                if (!empty($meta['issued_to'])) {
                    $user = get_userdata($meta['issued_to']);
                    $issued_to_name = $user ? $user->display_name : __('Unknown User', 'asset-manager-mvc');
                }
                $categories = get_the_terms($post_id, $taxonomy_slug);
                $category_name = (!empty($categories) && !is_wp_error($categories)) ? esc_html(implode(', ', wp_list_pluck($categories, 'name'))) : '—';
                ?>
                <tr>
                    <td><?php echo esc_html(get_the_title()); ?></td>
                    <td><?php echo esc_html($meta['asset_tag']); ?></td>
                    <td><?php echo esc_html($meta['model']); ?></td>
                    <td><?php echo esc_html($meta['serial_number']); ?></td>
                    <td><?php echo esc_html($meta['brand']); ?></td>
                    <td><?php echo $category_name; // Already escaped ?></td>
                    <td><?php echo esc_html($meta['status']); ?></td>
                    <td><?php echo esc_html($issued_to_name); ?></td>
                    <td><?php echo esc_html($meta['date_purchased']); ?></td>
                    <td><?php echo nl2br(esc_html($meta['description'])); ?></td>
                </tr>
            <?php endwhile; ?>
            <?php wp_reset_postdata(); ?>
        <?php else : ?>
            <tr>
                <td colspan="10" class="no-assets"><?php esc_html_e('No assets found.', 'asset-manager-mvc'); ?></td>
            </tr>
        <?php endif; ?>
    </tbody>
</table>
"""

# Placeholder Contents
placeholder_css_content = """/*
Asset Manager MVC Admin Styles
*/
.asset-fields .required {
    color: red;
    margin-left: 2px;
}

.asset-manager-dashboard .dashboard-widgets-wrapper {
    display: flex;
    flex-wrap: wrap;
    gap: 20px;
}

.asset-manager-dashboard .dashboard-widget {
    flex: 1 1 300px; /* Adjust basis for responsiveness */
    border: 1px solid #ccd0d4;
    padding: 15px;
    background-color: #fff;
    box-shadow: 0 1px 1px rgba(0,0,0,.04);
}

.asset-manager-dashboard .dashboard-widget h2 {
    margin-top: 0;
    font-size: 16px;
    border-bottom: 1px solid #eee;
    padding-bottom: 10px;
    margin-bottom: 15px;
}

.asset-manager-dashboard .chart-container {
    position: relative;
    height: 300px; /* Adjust as needed */
    width: 100%;
}

.asset-history {
    list-style: disc;
    margin-left: 20px;
}
.asset-history li {
    margin-bottom: 8px;
    padding-bottom: 8px;
    border-bottom: 1px dotted #eee;
}
.asset-history li:last-child {
    border-bottom: none;
}
"""

placeholder_admin_js_content = """// Asset Manager MVC Admin JavaScript
jQuery(document).ready(function($) {
    // console.log('Asset Manager MVC Admin JS Loaded');
    // Add any specific admin interactivity here, for example:
    // - Date picker initialization if not using type="date"
    // - Conditional logic for fields
});
"""

placeholder_dashboard_js_content = """// Asset Manager MVC Dashboard JavaScript
jQuery(document).ready(function($) {
    // console.log('Asset Manager MVC Dashboard JS Loaded');
    // console.log(assetDashboardData); // Check localized data

    if (typeof Chart !== 'undefined' && typeof assetDashboardData !== 'undefined') {
        // Helper function to generate random colors for charts
        const generateChartColors = (numColors) => {
            const colors = [];
            for (let i = 0; i < numColors; i++) {
                colors.push(`hsl(${(i * 360 / numColors) % 360}, 70%, 60%)`);
            }
            return colors;
        };

        // Assets by Status Chart
        const statusCtx = document.getElementById('assetMvcStatusChart');
        if (statusCtx && assetDashboardData.status) {
            const statusLabels = Object.keys(assetDashboardData.status);
            const statusCounts = Object.values(assetDashboardData.status);
            new Chart(statusCtx, {
                type: 'doughnut', // or 'pie'
                data: {
                    labels: statusLabels,
                    datasets: [{
                        label: 'Assets by Status',
                        data: statusCounts,
                        backgroundColor: generateChartColors(statusLabels.length),
                        hoverOffset: 4
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: {
                            position: 'top',
                        },
                        title: {
                            display: false,
                            text: 'Assets by Status'
                        }
                    }
                }
            });
        }

        // Assets by User Chart
        const userCtx = document.getElementById('assetMvcUserChart');
        if (userCtx && assetDashboardData.users) {
            const userLabels = Object.keys(assetDashboardData.users);
            const userCounts = Object.values(assetDashboardData.users);
            new Chart(userCtx, {
                type: 'bar',
                data: {
                    labels: userLabels,
                    datasets: [{
                        label: 'Assets by User',
                        data: userCounts,
                        backgroundColor: generateChartColors(userLabels.length),
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    scales: {
                        y: {
                            beginAtZero: true,
                            ticks: {
                                stepSize: 1 // Ensure whole numbers for counts
                            }
                        }
                    },
                    plugins: {
                        legend: {
                            display: false,
                        },
                         title: {
                            display: false,
                            text: 'Assets by User'
                        }
                    }
                }
            });
        }

        // Assets by Category Chart
        const categoryCtx = document.getElementById('assetMvcCategoryChart');
        if (categoryCtx && assetDashboardData.categories) {
            const categoryLabels = Object.keys(assetDashboardData.categories);
            const categoryCounts = Object.values(assetDashboardData.categories);
            new Chart(categoryCtx, {
                type: 'pie', // or 'doughnut'
                data: {
                    labels: categoryLabels,
                    datasets: [{
                        label: 'Assets by Category',
                        data: categoryCounts,
                        backgroundColor: generateChartColors(categoryLabels.length),
                        hoverOffset: 4
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: {
                            position: 'top',
                        },
                         title: {
                            display: false,
                            text: 'Assets by Category'
                        }
                    }
                }
            });
        }

    } else {
        if (typeof Chart === 'undefined') {
            console.error('Chart.js is not loaded.');
        }
        if (typeof assetDashboardData === 'undefined') {
            console.error('assetDashboardData is not defined. Check wp_localize_script.');
        }
    }
});
"""

placeholder_pot_content = """# Copyright (C) YEAR THE PACKAGE'S COPYRIGHT HOLDER
# This file is distributed under the same license as the PACKAGE package.
# FIRST AUTHOR <EMAIL@ADDRESS>, YEAR.
#
#, fuzzy
msgid ""
msgstr ""
"Project-Id-Version: asset-manager-mvc 1.9.0\\n"
"Report-Msgid-Bugs-To: \\n"
"POT-Creation-Date: YYYY-MM-DD HH:MM+ZZZZ\\n"
"PO-Revision-Date: YEAR-MO-DA HO:MI+ZONE\\n"
"Last-Translator: FULL NAME <EMAIL@ADDRESS>\\n"
"Language-Team: LANGUAGE <LL@li.org>\\n"
"Language: \\n"
"MIME-Version: 1.0\\n"
"Content-Type: text/plain; charset=UTF-8\\n"
"Content-Transfer-Encoding: 8bit\\n"
"Plural-Forms: nplurals=INTEGER; plural=EXPRESSION;\\n"

#. Plugin Name of the plugin/theme
msgid "Asset Manager (MVC)"
msgstr ""

#. Description of the plugin/theme
msgid "Custom post type for managing assets with history tracking, custom fields, PDF export, and more (MVC Structure)."
msgstr ""

#. Author of the plugin/theme
msgid "Your Name"
msgstr ""

# Add other translatable strings here as they appear in your __() and _e() calls.
# Example:
# msgid "Asset Tag"
# msgstr ""
"""


# --- Script Logic ---

def create_plugin_file(path, content):
    """Creates a file with the given content, ensuring parent directories exist."""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(textwrap.dedent(content))
    print(f"Created: {path}")

def main():
    plugin_base_dir = "asset-manager-mvc"
    if os.path.exists(plugin_base_dir):
        print(f"Directory '{plugin_base_dir}' already exists. Please remove or rename it before running this script.")
        # For safety, we could add shutil.rmtree(plugin_base_dir) here, but it's better to let the user handle it.
        # return

    # Define file structure and content
    files_to_create = {
        # Main plugin file
        f"{plugin_base_dir}/asset-manager.php": asset_manager_php_content,

        # Core
        f"{plugin_base_dir}/includes/core/class-plugin-core.php": plugin_core_php_content,

        # Models
        f"{plugin_base_dir}/includes/models/class-asset-model.php": asset_model_php_content,

        # Controllers
        f"{plugin_base_dir}/includes/controllers/class-setup-controller.php": setup_controller_php_content,
        f"{plugin_base_dir}/includes/controllers/class-asset-controller.php": asset_controller_php_content,
        f"{plugin_base_dir}/includes/controllers/class-dashboard-controller.php": dashboard_controller_php_content,
        f"{plugin_base_dir}/includes/controllers/class-export-controller.php": export_controller_php_content,

        # Views - Admin
        f"{plugin_base_dir}/includes/views/admin/asset-fields-meta-box.php": view_asset_fields_php_content,
        f"{plugin_base_dir}/includes/views/admin/asset-history-meta-box.php": view_asset_history_php_content,
        f"{plugin_base_dir}/includes/views/admin/dashboard-page.php": view_dashboard_page_php_content,
        f"{plugin_base_dir}/includes/views/admin/export-page.php": view_export_page_php_content,
        f"{plugin_base_dir}/includes/views/admin/notices/validation-errors.php": view_validation_errors_php_content,

        # Views - PDF
        f"{plugin_base_dir}/includes/views/pdf/asset-export-template.php": view_pdf_template_php_content,

        # Assets (Placeholders)
        f"{plugin_base_dir}/assets/css/asset-manager-admin.css": placeholder_css_content,
        f"{plugin_base_dir}/assets/js/asset-manager-admin.js": placeholder_admin_js_content,
        f"{plugin_base_dir}/assets/js/asset-dashboard.js": placeholder_dashboard_js_content,

        # Languages (Placeholder)
        f"{plugin_base_dir}/languages/asset-manager-mvc.pot": placeholder_pot_content,
        f"{plugin_base_dir}/languages/index.php": "<?php // Silence is golden.", # Common practice for WP directories
        f"{plugin_base_dir}/assets/index.php": "<?php // Silence is golden.",
        f"{plugin_base_dir}/includes/index.php": "<?php // Silence is golden.",
        f"{plugin_base_dir}/includes/core/index.php": "<?php // Silence is golden.",
        f"{plugin_base_dir}/includes/models/index.php": "<?php // Silence is golden.",
        f"{plugin_base_dir}/includes/controllers/index.php": "<?php // Silence is golden.",
        f"{plugin_base_dir}/includes/views/index.php": "<?php // Silence is golden.",
        f"{plugin_base_dir}/includes/views/admin/index.php": "<?php // Silence is golden.",
        f"{plugin_base_dir}/includes/views/admin/notices/index.php": "<?php // Silence is golden.",
        f"{plugin_base_dir}/includes/views/pdf/index.php": "<?php // Silence is golden.",
    }

    # Create all files
    for path, content in files_to_create.items():
        create_plugin_file(path, content)

    # Create vendor directory (usually for Composer dependencies like mPDF)
    os.makedirs(os.path.join(plugin_base_dir, "vendor"), exist_ok=True)
    create_plugin_file(os.path.join(plugin_base_dir, "vendor", "index.php"), "<?php // Silence is golden.")
    print(f"Created: {plugin_base_dir}/vendor/ (Note: mPDF should be installed here, typically via Composer)")


    # Create ZIP file
    zip_file_name = f"{plugin_base_dir}.zip"
    with zipfile.ZipFile(zip_file_name, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(plugin_base_dir):
            for file in files:
                file_path = os.path.join(root, file)
                # Arcname is the path inside the zip file
                arcname = os.path.relpath(file_path, os.path.join(plugin_base_dir, '..'))
                zipf.write(file_path, arcname)
    
    print(f"Successfully created plugin structure in '{plugin_base_dir}'")
    print(f"ZIP file created: {zip_file_name}")
    print(f"Reminder: If you are not using Composer, you will need to manually add the mPDF library to the '{plugin_base_dir}/vendor/' directory and adjust the autoloader path in 'includes/controllers/class-export-controller.php' if necessary.")

if __name__ == "__main__":
    main()
