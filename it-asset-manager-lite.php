<?php
/**
 * Plugin Name: Asset Manager
 * Description: Custom post type for managing assets with history tracking, custom fields, PDF export, and more.
 * Version: 1.8.4
 * Author: Your Name
 * Text Domain: asset-manager
 * Domain Path: /languages
 */

if (!defined('ABSPATH')) exit; // Exit if accessed directly

// Define constants
define('ASSET_MANAGER_VERSION', '1.8.4'); // MODIFIED version - Added filters and enhanced search
define('ASSET_MANAGER_POST_TYPE', 'asset');
define('ASSET_MANAGER_TAXONOMY', 'asset_category');
define('ASSET_MANAGER_META_PREFIX', '_asset_manager_');

class Asset_Manager {
    // Auto-increment title for Asset post type in format 00001, 00002, ...
    public function auto_increment_title($data, $postarr) {
        if ($data['post_type'] !== ASSET_MANAGER_POST_TYPE) {
            return $data;
        }

        // Only modify title on auto-draft or if title is empty (new post)
        if ($data['post_status'] === 'auto-draft' || !empty($data['post_title'])) {
            return $data;
        }

        // Get the latest asset post by title in descending order
        $args = [
            'post_type'      => ASSET_MANAGER_POST_TYPE,
            'post_status'    => 'publish',
            'posts_per_page' => 1,
            'orderby'        => 'title',
            'order'          => 'DESC',
            'fields'         => 'ids',
        ];

        $latest = get_posts($args);
        $last_number = 0;

        if (!empty($latest)) {
            $last_post = get_post($latest[0]);
            if (preg_match('/^0*(\\d+)$/', $last_post->post_title, $matches)) {
                $last_number = intval($matches[1]);
            }
        }

        $next_number = $last_number + 1;
        $data['post_title'] = str_pad($next_number, 5, '0', STR_PAD_LEFT);

        return $data;
    }


    public function add_image_meta_box() {
        add_meta_box(
            'asset_image',
            __('Asset Image', 'asset-manager'),
            [$this, 'render_image_meta_box'],
            ASSET_MANAGER_POST_TYPE,
            'side',
            'default'
        );
    }

    public function render_image_meta_box($post) {
        $image_id = get_post_meta($post->ID, '_asset_image_id', true);
        $image_url = $image_id ? wp_get_attachment_url($image_id) : '';

        wp_nonce_field('save_asset_image', 'asset_image_nonce');
        ?>
        <div>
            <img id="asset-image-preview" src="<?php echo esc_url($image_url); ?>" style="max-width:100%;<?php echo empty($image_url) ? 'display:none;' : ''; ?>" />
            <input type="hidden" name="asset_image_id" id="asset-image-id" value="<?php echo esc_attr($image_id); ?>" />
            <button type="button" class="button" id="upload-asset-image"><?php _e('Upload Image', 'asset-manager'); ?></button>
            <button type="button" class="button" id="remove-asset-image" style="<?php echo empty($image_url) ? 'display:none;' : ''; ?>"><?php _e('Remove Image', 'asset-manager'); ?></button>
        </div>
        <script>
            jQuery(document).ready(function($){
                var mediaUploader;

                $('#upload-asset-image').click(function(e) {
                    e.preventDefault();
                    if (mediaUploader) {
                        mediaUploader.open();
                        return;
                    }
                    mediaUploader = wp.media({
                        title: 'Select Asset Image',
                        button: { text: 'Use this image' },
                        multiple: false
                    });

                    mediaUploader.on('select', function() {
                        var attachment = mediaUploader.state().get('selection').first().toJSON();
                        $('#asset-image-id').val(attachment.id);
                        $('#asset-image-preview').attr('src', attachment.url).show();
                        $('#remove-asset-image').show();
                    });

                    mediaUploader.open();
                });

                $('#remove-asset-image').click(function() {
                    $('#asset-image-id').val('');
                    $('#asset-image-preview').hide();
                    $(this).hide();
                });
            });
        </script>
        <?php
    }

    public function save_asset_image($post_id) {
        if (!isset($_POST['asset_image_nonce']) || !wp_verify_nonce($_POST['asset_image_nonce'], 'save_asset_image')) return;
        if (defined('DOING_AUTOSAVE') && DOING_AUTOSAVE) return;
        if (!current_user_can('edit_post', $post_id)) return;

        $image_id = isset($_POST['asset_image_id']) ? intval($_POST['asset_image_id']) : '';
        if ($image_id) {
            update_post_meta($post_id, '_asset_image_id', $image_id);
        } else {
            delete_post_meta($post_id, '_asset_image_id');
        }
    }

    public function enqueue_media_uploader($hook) {
        if ($hook === 'post-new.php' || $hook === 'post.php') {
            global $post;
            if ($post && $post->post_type === ASSET_MANAGER_POST_TYPE) {
                wp_enqueue_media();
            }
        }
    }


    // IMPROVEMENT: Model is now the second field.
    // MODIFICATION: Added 'location' field
    private $fields = [
        'asset_tag', 'model', 'serial_number', 'brand', 'supplier',
        'date_purchased', 'issued_to', 'status', 'location', 'description'
    ];

    // IMPROVEMENT: "Unassigned" added as the first status option.
    private $status_options = ['Unassigned', 'Assigned', 'Returned', 'For Repair', 'Repairing', 'Archived', 'Disposed'];

    public function __construct() {
        add_action('add_meta_boxes', [$this, 'add_image_meta_box']);
        add_action('admin_enqueue_scripts', [$this, 'enqueue_media_uploader']);
        add_action('save_post', [$this, 'save_asset_image']);

        register_activation_hook(__FILE__, [$this, 'activate']);
        add_action('init', [$this, 'load_plugin_textdomain']);
        add_action('init', [$this, 'register_asset_post_type']);
        add_action('init', [$this, 'register_asset_taxonomy']);
        add_action('init', [$this, 'register_shortcodes']); // Assumed to be implemented or placeholder
        if (is_admin()) {
            add_action('add_meta_boxes', [$this, 'register_meta_boxes']);
            add_action('save_post_' . ASSET_MANAGER_POST_TYPE, [$this, 'save_asset_meta'], 10, 2);
            add_filter('manage_' . ASSET_MANAGER_POST_TYPE . '_posts_columns', [$this, 'custom_columns']);
            add_action('manage_' . ASSET_MANAGER_POST_TYPE . '_posts_custom_column', [$this, 'custom_column_content'], 10, 2);
            add_action('admin_menu', [$this, 'register_admin_pages']);
            add_action('admin_post_am_export_assets_pdf_action', [$this, 'export_assets_pdf']);
            add_action('admin_enqueue_scripts', [$this, 'enqueue_admin_assets']);
            add_action('admin_notices', [$this, 'display_admin_notices']);

            // New actions for filters and search
            add_action('restrict_manage_posts', [$this, 'add_asset_filters_to_admin_list']);
            add_action('pre_get_posts', [$this, 'filter_assets_query']);
            add_action('pre_get_posts', [$this, 'extend_asset_search_query']);
        }
    }

    private function get_field_labels() {
        // Order of labels here doesn't affect display order in meta box,
        // that's controlled by $this->fields and the HTML structure in render_asset_fields_meta_box
        // MODIFICATION: Added 'location' label
        return [
            'asset_tag'     => __('Asset Tag', 'asset-manager'),
            'serial_number' => __('Serial Number', 'asset-manager'),
            'brand'         => __('Brand', 'asset-manager'),
            'model'         => __('Model', 'asset-manager'),
            'supplier'      => __('Supplier', 'asset-manager'),
            'date_purchased'=> __('Date Purchased', 'asset-manager'),
            'issued_to'     => __('Issued To', 'asset-manager'),
            'status'        => __('Status', 'asset-manager'),
            'location'      => __('Location', 'asset-manager'), // New field label
            'description'   => __('Description', 'asset-manager'),
            ASSET_MANAGER_META_PREFIX . 'asset_category' => __('Category', 'asset-manager'),
        ];
    }

    public function activate() {
        $this->register_asset_post_type();
        $this->register_asset_taxonomy();
        flush_rewrite_rules();
    }

    public function load_plugin_textdomain() {
        load_plugin_textdomain('asset-manager', false, dirname(plugin_basename(__FILE__)) . '/languages/');
    }

    public function enqueue_admin_assets($hook) {
        global $post_type, $pagenow;

        $is_asset_manager_cpt_screen = ($post_type === ASSET_MANAGER_POST_TYPE && in_array($pagenow, ['post.php', 'post-new.php']));
        $is_asset_manager_list_screen = ($pagenow === 'edit.php' && isset($_GET['post_type']) && $_GET['post_type'] === ASSET_MANAGER_POST_TYPE);
        $is_asset_manager_dashboard_screen = strpos($hook, ASSET_MANAGER_POST_TYPE.'_page_asset_dashboard') !== false;
        $is_asset_manager_export_screen = strpos($hook, ASSET_MANAGER_POST_TYPE.'_page_export-assets') !== false;

        if ($is_asset_manager_cpt_screen || $is_asset_manager_dashboard_screen || $is_asset_manager_export_screen || $is_asset_manager_list_screen) {
            wp_enqueue_style('asset-manager-admin-css', plugin_dir_url(__FILE__) . 'css/asset-manager.css', [], ASSET_MANAGER_VERSION);
        }
        
        if ($is_asset_manager_list_screen) {
             // Potentially add JS for select2 if desired for filters, not strictly necessary for basic dropdowns
        }

        if ($is_asset_manager_dashboard_screen) {
            wp_enqueue_script('chart-js', 'https://cdn.jsdelivr.net/npm/chart.js', [], '4.4.1', true);
            wp_enqueue_script('asset-dashboard-js', plugin_dir_url(__FILE__) . 'js/asset-dashboard.js', ['jquery', 'chart-js'], ASSET_MANAGER_VERSION, true);
            wp_localize_script('asset-dashboard-js', 'assetDashboardData', $this->get_dashboard_data());
        }

        if ($is_asset_manager_cpt_screen) {
            wp_enqueue_script('asset-manager-admin-js', plugin_dir_url(__FILE__) . 'js/asset-manager-admin.js', ['jquery'], ASSET_MANAGER_VERSION, true);
        }
    }

    public function register_asset_post_type() {
        $labels = [ 'name' => _x('Assets', 'post type general name', 'asset-manager'), 'singular_name' => _x('Asset', 'post type singular name', 'asset-manager'), 'menu_name' => _x('Assets', 'admin menu', 'asset-manager'), 'name_admin_bar' => _x('Asset', 'add new on admin bar', 'asset-manager'), 'add_new' => _x('Add New', 'asset', 'asset-manager'), 'add_new_item' => __('Add New Asset', 'asset-manager'), 'new_item' => __('New Asset', 'asset-manager'), 'edit_item' => __('Edit Asset', 'asset-manager'), 'view_item' => __('View Asset', 'asset-manager'), 'all_items' => __('All Assets', 'asset-manager'), 'search_items' => __('Search Assets', 'asset-manager'), 'parent_item_colon' => __('Parent Assets:', 'asset-manager'), 'not_found' => __('No assets found.', 'asset-manager'), 'not_found_in_trash' => __('No assets found in Trash.', 'asset-manager'), 'attributes' => __( 'Asset Attributes', 'asset-manager' ), ];
        $args = [ 'labels' => $labels, 'public' => false, 'show_ui' => true, 'show_in_menu' => true, 'query_var' => true, 'rewrite' => ['slug' => ASSET_MANAGER_POST_TYPE], 'capability_type' => 'post', 'has_archive' => false, 'hierarchical' => false, 'menu_position' => 20, 'supports' => ['title'], 'menu_icon' => 'dashicons-archive', 'show_in_rest' => true, ];
        register_post_type(ASSET_MANAGER_POST_TYPE, $args);
    }

    public function register_asset_taxonomy() {
        $labels = [ 'name' => _x('Asset Categories', 'taxonomy general name', 'asset-manager'), 'singular_name' => _x('Asset Category', 'taxonomy singular name', 'asset-manager'), 'search_items' => __('Search Asset Categories', 'asset-manager'), 'all_items' => __('All Asset Categories', 'asset-manager'), 'parent_item' => __('Parent Asset Category', 'asset-manager'), 'parent_item_colon' => __('Parent Asset Category:', 'asset-manager'), 'edit_item' => __('Edit Asset Category', 'asset-manager'), 'update_item' => __('Update Asset Category', 'asset-manager'), 'add_new_item' => __('Add New Asset Category', 'asset-manager'), 'new_item_name' => __('New Asset Category Name', 'asset-manager'), 'menu_name' => __('Categories', 'asset-manager'), ];
        $args = [ 'hierarchical' => true, 'labels' => $labels, 'show_ui' => true, 'show_admin_column' => true, 'query_var' => true, 'rewrite' => ['slug' => ASSET_MANAGER_TAXONOMY], 'show_in_rest' => true, ];
        register_taxonomy(ASSET_MANAGER_TAXONOMY, ASSET_MANAGER_POST_TYPE, $args);
    }

    public function register_meta_boxes() {
        add_meta_box(ASSET_MANAGER_META_PREFIX . 'details', __('Asset Details', 'asset-manager'), [$this, 'render_asset_fields_meta_box'], ASSET_MANAGER_POST_TYPE, 'normal', 'high');
        add_meta_box(ASSET_MANAGER_META_PREFIX . 'history', __('Asset History', 'asset-manager'), [$this, 'render_history_meta_box'], ASSET_MANAGER_POST_TYPE, 'normal', 'default');
    }

    public function render_asset_fields_meta_box($post) {
        wp_nonce_field(ASSET_MANAGER_META_PREFIX . 'save_details_nonce', ASSET_MANAGER_META_PREFIX . 'details_nonce');
        $meta_values = [];
        // Fetch all meta values at once to be slightly more efficient if WordPress doesn't cache them aggressively for individual get_post_meta calls
        $all_meta = get_post_meta($post->ID);
        foreach ($this->fields as $field_key) {
            $meta_key_with_prefix = ASSET_MANAGER_META_PREFIX . $field_key;
            $meta_values[$field_key] = isset($all_meta[$meta_key_with_prefix][0]) ? $all_meta[$meta_key_with_prefix][0] : '';
        }

        $users = get_users(['orderby' => 'display_name']);
        $categories = get_terms(['taxonomy' => ASSET_MANAGER_TAXONOMY, 'hide_empty' => false]);
        $field_labels = $this->get_field_labels(); // Get labels for consistent display
        ?>
        <div class="asset-fields">
            <?php foreach ($this->fields as $field_key) :
                $field_id = 'am_' . str_replace('_', '-', $field_key); // e.g., am_asset-tag
                $field_name = ASSET_MANAGER_META_PREFIX . $field_key;
                $label_text = isset($field_labels[$field_key]) ? $field_labels[$field_key] : ucfirst(str_replace('_', ' ', $field_key));
                $value = $meta_values[$field_key];
            ?>
            <p>
                <label for="<?php echo esc_attr($field_id); ?>"><?php echo esc_html($label_text); ?>: <span class="required">*</span></label>
                <?php if ($field_key === 'issued_to') : ?>
                    <select id="<?php echo esc_attr($field_id); ?>" name="<?php echo esc_attr($field_name); ?>" class="widefat" required>
                        <option value=""><?php esc_html_e('-- Select User --', 'asset-manager'); ?></option>
                        <?php foreach ($users as $user): ?>
                            <option value="<?php echo esc_attr($user->ID); ?>" <?php selected($value, $user->ID); ?>>
                                <?php echo esc_html($user->display_name . ' (' . $user->user_email . ')'); ?>
                            </option>
                        <?php endforeach; ?>
                    </select>
                <?php elseif ($field_key === 'status') : ?>
                    <select id="<?php echo esc_attr($field_id); ?>" name="<?php echo esc_attr($field_name); ?>" class="widefat" required>
                        <option value=""><?php esc_html_e('-- Select Status --', 'asset-manager'); ?></option>
                        <?php foreach ($this->status_options as $status_option) : ?>
                            <option value="<?php echo esc_attr($status_option); ?>" <?php selected($value, $status_option); ?>>
                                <?php echo esc_html($status_option); // Assuming status options are not needing translation here, if they do, they should be wrapped in __() when defined or here. ?>
                            </option>
                        <?php endforeach; ?>
                    </select>
                <?php elseif ($field_key === 'description') : ?>
                    <textarea id="<?php echo esc_attr($field_id); ?>" name="<?php echo esc_attr($field_name); ?>" class="widefat" rows="5" required><?php echo esc_textarea($value); ?></textarea>
                <?php elseif ($field_key === 'date_purchased') : ?>
                    <input type="date" id="<?php echo esc_attr($field_id); ?>" name="<?php echo esc_attr($field_name); ?>" value="<?php echo esc_attr($value); ?>" class="widefat" required>
                <?php else : // For asset_tag, serial_number, brand, model, supplier, location ?>
                    <input type="text" id="<?php echo esc_attr($field_id); ?>" name="<?php echo esc_attr($field_name); ?>" value="<?php echo esc_attr($value); ?>" class="widefat" required>
                <?php endif; ?>
            </p>
            <?php endforeach; ?>

            <p>
                <label for="am_asset_category"><?php esc_html_e('Category:', 'asset-manager'); ?> <span class="required">*</span></label>
                <select id="am_asset_category" name="<?php echo ASSET_MANAGER_META_PREFIX; ?>asset_category" class="widefat" required>
                    <option value=""><?php esc_html_e('-- Select Category --', 'asset-manager'); ?></option>
                    <?php foreach ($categories as $cat): ?>
                        <option value="<?php echo esc_attr($cat->term_id); ?>" <?php selected(has_term($cat->term_id, ASSET_MANAGER_TAXONOMY, $post)); ?>>
                            <?php echo esc_html($cat->name); ?>
                        </option>
                    <?php endforeach; ?>
                </select>
            </p>
        </div>
        <?php
        // Inline style removed. Add '.required { color: red; margin-left: 2px;}' to your asset-manager-admin.css file.
    }


    public function render_history_meta_box($post) {
        $history = get_post_meta($post->ID, ASSET_MANAGER_META_PREFIX . 'history', true);
        if (empty($history) || !is_array($history)) { echo '<p>' . esc_html__('No history available.', 'asset-manager') . '</p>'; return; }
        echo '<ul class="asset-history">';
        foreach (array_reverse($history) as $entry) { 
            $user_info = ''; if (!empty($entry['user'])) { $user_data = get_userdata($entry['user']); if ($user_data) { $user_info = ' (' . esc_html($user_data->display_name) . ')'; } }
            $formatted_date = !empty($entry['date']) ? mysql2date(get_option('date_format') . ' @ ' . get_option('time_format'), $entry['date']) : __('Unknown Date', 'asset-manager');
            echo '<li><strong>' . esc_html($formatted_date) . esc_html($user_info) . ':</strong> ' . wp_kses_post($entry['note']) . '</li>';
        } echo '</ul>';
    }

    // MODIFICATION: Added validation for 'location'
    private function _validate_asset_data(array $form_data): array {
        $errors = [];
        $field_labels = $this->get_field_labels();

        foreach ($this->fields as $field_key) {
            $post_field_key = ASSET_MANAGER_META_PREFIX . $field_key;
            $value = isset($form_data[$post_field_key]) ? trim($form_data[$post_field_key]) : '';

            if ($field_key === 'date_purchased') {
                if (empty($value)) {
                    $errors[] = sprintf(__('The %s field is required.', 'asset-manager'), $field_labels[$field_key]);
                } else {
                    $date = DateTime::createFromFormat('Y-m-d', $value);
                    if (!$date || $date->format('Y-m-d') !== $value) {
                        $errors[] = sprintf(__('The %s field has an invalid date format. Please use YYYY-MM-DD.', 'asset-manager'), $field_labels[$field_key]);
                    }
                }
            } elseif ($field_key === 'status') { // Status is a select, empty value means "-- Select Status --"
                 if ($value === '') {
                     $errors[] = sprintf(__('The %s field is required; please select a status.', 'asset-manager'), $field_labels[$field_key]);
                 } elseif (!in_array($value, $this->status_options, true)) {
                     $errors[] = sprintf(__('Invalid value selected for the %s field.', 'asset-manager'), $field_labels[$field_key]);
                 }
            } elseif (empty($value) && $value !== '0') { // Standard required field check, applies to 'location' too
                if ($field_key === 'issued_to' && $form_data[$post_field_key] === '') {
                    // Allow 'issued_to' to be empty if status is 'Unassigned'
                    $status_value = isset($form_data[ASSET_MANAGER_META_PREFIX . 'status']) ? trim($form_data[ASSET_MANAGER_META_PREFIX . 'status']) : '';
                    if ($status_value !== 'Unassigned') {
                        $errors[] = sprintf(__('The %s field is required; please select a user.', 'asset-manager'), $field_labels[$field_key]);
                    }
                } elseif ($field_key !== 'issued_to') { // All other text fields including 'location'
                    $errors[] = sprintf(__('The %s field is required.', 'asset-manager'), $field_labels[$field_key]);
                }
            }
        }

        $category_post_key = ASSET_MANAGER_META_PREFIX . 'asset_category';
        $category_value = isset($form_data[$category_post_key]) ? $form_data[$category_post_key] : '';
        if (empty($category_value)) {
            $errors[] = sprintf(__('The %s field is required; please select a category.', 'asset-manager'), $field_labels[$category_post_key]);
        }
        return $errors;
    }


    // MODIFICATION: Added save and history tracking for 'location'
    public function save_asset_meta($post_id, $post) {
        if (!isset($_POST[ASSET_MANAGER_META_PREFIX . 'details_nonce']) || !wp_verify_nonce($_POST[ASSET_MANAGER_META_PREFIX . 'details_nonce'], ASSET_MANAGER_META_PREFIX . 'save_details_nonce')) { return; }
        if (!current_user_can('edit_post', $post_id)) { return; }
        if (defined('DOING_AUTOSAVE') && DOING_AUTOSAVE) { return; }
        if ($post->post_type !== ASSET_MANAGER_POST_TYPE) { return; }

        $errors = $this->_validate_asset_data($_POST);
        
        if (!empty($errors)) {
            set_transient('asset_manager_errors_' . $post_id . '_' . get_current_user_id(), $errors, 45);
            // Ensure redirect_post_location filter is added only once if multiple saves happen quickly (though less likely for manual post saving)
            if (!has_filter('redirect_post_location', 'asset_manager_redirect_on_error_fix')) {
                 add_filter('redirect_post_location', function($location) use ($post_id) {
                    // Check the transient with the same key used for setting it.
                    if (get_transient('asset_manager_errors_' . $post_id . '_' . get_current_user_id())) {
                        $location = remove_query_arg('message', $location);
                    }
                    return $location;
                }, 99, 1);
            }
            return;
        }


        $changes = [];
        $current_history = get_post_meta($post_id, ASSET_MANAGER_META_PREFIX . 'history', true) ?: [];
        if (!is_array($current_history)) $current_history = [];
        $field_labels = $this->get_field_labels();
        $current_status = isset($_POST[ASSET_MANAGER_META_PREFIX . 'status']) ? sanitize_text_field($_POST[ASSET_MANAGER_META_PREFIX . 'status']) : null;


        foreach ($this->fields as $field_key) {
            $meta_key = ASSET_MANAGER_META_PREFIX . $field_key;
            $new_value_raw = isset($_POST[$meta_key]) ? $_POST[$meta_key] : null;
            $old_value = get_post_meta($post_id, $meta_key, true);
            $new_value_sanitized = '';

            switch ($field_key) {
                case 'description':
                    $new_value_sanitized = sanitize_textarea_field($new_value_raw);
                    break;
                case 'date_purchased':
                    if (is_string($new_value_raw)) {
                        $date = DateTime::createFromFormat('Y-m-d', $new_value_raw);
                        if ($date && $date->format('Y-m-d') === $new_value_raw) {
                            $new_value_sanitized = $new_value_raw;
                        } else {
                            $new_value_sanitized = ''; 
                        }
                    } else {
                        $new_value_sanitized = '';
                    }
                    break;
                case 'issued_to':
                    // If status is 'Unassigned', 'issued_to' can be empty. Otherwise, it's absint.
                     $new_value_sanitized = ($current_status === 'Unassigned' && empty($new_value_raw)) ? '' : absint($new_value_raw);
                    break;
                case 'status': // Ensure the status is one of the predefined options
                    $new_value_sanitized = in_array($new_value_raw, $this->status_options, true) ? sanitize_text_field($new_value_raw) : $this->status_options[0]; // Default to first option (Unassigned) if invalid
                    break;
                // case 'location': // Covered by default sanitize_text_field
                default: 
                    $new_value_sanitized = sanitize_text_field($new_value_raw);
                    break;
            }

            $old_value_comparable = $old_value;
            $new_value_comparable = $new_value_sanitized;

            if ($field_key === 'issued_to') {
                $old_value_comparable = ($old_value === '' || $old_value === '0') ? '' : absint($old_value);
                $new_value_comparable = ($new_value_comparable === '' || $new_value_comparable === 0) ? '' : absint($new_value_comparable);

            } elseif (is_string($old_value_comparable) && is_string($new_value_comparable)) {
                $old_value_comparable = trim($old_value_comparable);
                $new_value_comparable = trim($new_value_comparable);
            }


            if ($new_value_comparable !== $old_value_comparable) {
                update_post_meta($post_id, $meta_key, $new_value_sanitized);
                $label = $field_labels[$field_key];

                if ($field_key === 'description') {
                    $changes[] = sprintf(esc_html__('%1$s changed.', 'asset-manager'), esc_html($label));
                } elseif ($field_key === 'issued_to') {
                    $old_user_display = __('Unassigned', 'asset-manager');
                    if (!empty($old_value_comparable)) {
                        $old_user_data = get_userdata($old_value_comparable);
                        $old_user_display = $old_user_data ? $old_user_data->display_name : sprintf(__('Unknown User (ID: %s)', 'asset-manager'), $old_value_comparable);
                    }
                    $new_user_display = __('Unassigned', 'asset-manager'); 
                    if (!empty($new_value_comparable)) { 
                        $new_user_data = get_userdata($new_value_comparable);
                        $new_user_display = $new_user_data ? $new_user_data->display_name : sprintf(__('Unknown User (ID: %s)', 'asset-manager'), $new_value_comparable);
                    }
                    // Only log if there's a meaningful change (e.g. not from '' to 0 or vice-versa if they mean the same)
                    if ($old_user_display !== $new_user_display) {
                         $changes[] = sprintf(esc_html__('%1$s changed from "%2$s" to "%3$s"', 'asset-manager'), esc_html($label), esc_html($old_user_display), esc_html($new_user_display));
                    }
                } else { 
                    $old_display = (string)$old_value === '' ? __('empty', 'asset-manager') : (string)$old_value;
                    $new_display = (string)$new_value_sanitized === '' ? __('empty', 'asset-manager') : (string)$new_value_sanitized;
                    if ($old_display !== $new_display) { // Avoid logging if truly unchanged (e.g. empty string to empty string)
                        $changes[] = sprintf(esc_html__('%1$s changed from "%2$s" to "%3$s"', 'asset-manager'), esc_html($label), esc_html($old_display), esc_html($new_display));
                    }
                }
            }
        }

        $category_post_key = ASSET_MANAGER_META_PREFIX . 'asset_category';
        if (isset($_POST[$category_post_key])) {
            $new_term_id = absint($_POST[$category_post_key]);
            $old_terms = wp_get_post_terms($post_id, ASSET_MANAGER_TAXONOMY, ['fields' => 'ids']);
            $old_term_id = !empty($old_terms) && isset($old_terms[0]) ? absint($old_terms[0]) : 0;

            if ($new_term_id !== $old_term_id) {
                 wp_set_post_terms($post_id, ($new_term_id ? [$new_term_id] : []), ASSET_MANAGER_TAXONOMY, false);
                 $old_term_obj = $old_term_id ? get_term($old_term_id, ASSET_MANAGER_TAXONOMY) : null;
                 $new_term_obj = $new_term_id ? get_term($new_term_id, ASSET_MANAGER_TAXONOMY) : null;
                 $old_term_name = ($old_term_obj && !is_wp_error($old_term_obj)) ? $old_term_obj->name : __('None', 'asset-manager');
                 $new_term_name = ($new_term_obj && !is_wp_error($new_term_obj)) ? $new_term_obj->name : __('None', 'asset-manager');
                 $changes[] = sprintf(esc_html__('Category changed from "%1$s" to "%2$s"', 'asset-manager'), esc_html($old_term_name), esc_html($new_term_name));
            }
        }

        if (!empty($changes)) {
            $history_entry = ['date' => current_time('mysql'), 'user' => get_current_user_id(), 'note' => implode('; ', $changes)];
            $current_history[] = $history_entry;
            update_post_meta($post_id, ASSET_MANAGER_META_PREFIX . 'history', $current_history);
        }

        $post_obj = get_post($post_id);
        if ($post_obj && (empty($post_obj->post_title) || $post_obj->post_title === __('Auto Draft') || $post_obj->post_title === '')) {
            $asset_tag_val = get_post_meta($post_id, ASSET_MANAGER_META_PREFIX . 'asset_tag', true);
            $new_title = !empty($asset_tag_val) ? sprintf(__('Asset: %s', 'asset-manager'), $asset_tag_val) : sprintf(__('Asset #%d', 'asset-manager'), $post_id);
            
            // Temporarily remove the action to prevent recursion
            remove_action('save_post_' . ASSET_MANAGER_POST_TYPE, [$this, 'save_asset_meta'], 10);
            wp_update_post(['ID' => $post_id, 'post_title' => $new_title]);
            // Re-add the action
            add_action('save_post_' . ASSET_MANAGER_POST_TYPE, [$this, 'save_asset_meta'], 10, 2);
        }
    }

    public function display_admin_notices() {
        global $pagenow, $post;
        if (($pagenow == 'post.php' || $pagenow == 'post-new.php') && isset($post->ID) && isset($post->post_type) && $post->post_type == ASSET_MANAGER_POST_TYPE) {
            $transient_key = 'asset_manager_errors_' . $post->ID . '_' . get_current_user_id();
            $errors = get_transient($transient_key);
            if (!empty($errors) && is_array($errors)) {
                echo '<div id="message" class="notice notice-error is-dismissible"><p><strong>' . esc_html__('Please correct the following errors:', 'asset-manager') . '</strong></p><ul>';
                foreach ($errors as $error) { echo '<li>' . esc_html($error) . '</li>'; }
                echo '</ul></div>';
                delete_transient($transient_key);
            }
        }
    }
    
    // MODIFICATION: Added 'location' column
    public function custom_columns($columns) { 
        $new_columns = [ 
            'cb' => $columns['cb'], 
            'title' => __('Title', 'asset-manager'), 
            'asset_tag' => __('Asset Tag', 'asset-manager'), 
            'model' => __('Model', 'asset-manager'),
            'serial_number' => __('Serial Number', 'asset-manager'), 
            'brand' => __('Brand', 'asset-manager'), 
            'asset_category'=> __('Category', 'asset-manager'), 
            'location' => __('Location', 'asset-manager'), // New column
            'status' => __('Status', 'asset-manager'), 
            'issued_to' => __('Issued To', 'asset-manager'), 
            'date_purchased_col' => __('Date Purchased', 'asset-manager'), // New column for date purchased
            'date' => __('Date Created', 'asset-manager') // Original 'date' column (publish date)
        ]; 
        return $new_columns;
    }

    // MODIFICATION: Added content for 'location' column
    public function custom_column_content($column, $post_id) {
        switch ($column) {
            case 'asset_tag': echo esc_html(get_post_meta($post_id, ASSET_MANAGER_META_PREFIX . 'asset_tag', true)); break;
            case 'model': echo esc_html(get_post_meta($post_id, ASSET_MANAGER_META_PREFIX . 'model', true)); break;
            case 'serial_number': echo esc_html(get_post_meta($post_id, ASSET_MANAGER_META_PREFIX . 'serial_number', true)); break;
            case 'brand': echo esc_html(get_post_meta($post_id, ASSET_MANAGER_META_PREFIX . 'brand', true)); break;
            case 'asset_category': $terms = get_the_terms($post_id, ASSET_MANAGER_TAXONOMY); if (!empty($terms) && !is_wp_error($terms)) { echo esc_html(implode(', ', wp_list_pluck($terms, 'name'))); } else { echo '—'; } break;
            case 'location': echo esc_html(get_post_meta($post_id, ASSET_MANAGER_META_PREFIX . 'location', true)); break; 
            case 'status': echo esc_html(get_post_meta($post_id, ASSET_MANAGER_META_PREFIX . 'status', true)); break;
            case 'issued_to': 
                $user_id = get_post_meta($post_id, ASSET_MANAGER_META_PREFIX . 'issued_to', true); 
                if ($user_id) { 
                    $user = get_userdata($user_id); 
                    echo esc_html($user ? $user->display_name : __('Unknown User', 'asset-manager')); 
                } else { 
                    // Check if status is Unassigned
                    $status = get_post_meta($post_id, ASSET_MANAGER_META_PREFIX . 'status', true);
                    if ($status === 'Unassigned') {
                         echo __('Unassigned', 'asset-manager');
                    } else {
                        echo '—'; 
                    }
                } 
                break;
            case 'date_purchased_col': 
                $date_purchased = get_post_meta($post_id, ASSET_MANAGER_META_PREFIX . 'date_purchased', true);
                echo esc_html($date_purchased ? date_i18n(get_option('date_format'), strtotime($date_purchased)) : '—');
                break;
        }
    }

    public function register_admin_pages() { 
        add_submenu_page('edit.php?post_type=' . ASSET_MANAGER_POST_TYPE, __('Export Assets', 'asset-manager'), __('Export to PDF', 'asset-manager'), 'manage_options', 'export-assets', [$this, 'export_page_html']); add_submenu_page('edit.php?post_type=' . ASSET_MANAGER_POST_TYPE, __('Asset Dashboard', 'asset-manager'), __('Dashboard', 'asset-manager'), 'manage_options', 'asset_dashboard', [$this, 'render_dashboard_page']);
    }

    public function export_page_html() { 
        ?> <div class="wrap"> <h1><?php esc_html_e('Export Assets to PDF', 'asset-manager'); ?></h1> <form method="post" action="<?php echo esc_url(admin_url('admin-post.php')); ?>"> <input type="hidden" name="action" value="am_export_assets_pdf_action"> <?php wp_nonce_field('am_export_assets_pdf_nonce', 'am_export_nonce'); ?> <?php submit_button(__('Export All Assets as PDF', 'asset-manager')); ?> </form> </div> <?php
    }

    // MODIFICATION: Added 'location' to PDF export and updated colspan
    public function export_assets_pdf() {
        if (!isset($_POST['am_export_nonce']) || !wp_verify_nonce($_POST['am_export_nonce'], 'am_export_assets_pdf_nonce')) { wp_die(__('Security check failed.', 'asset-manager'), __('Error', 'asset-manager'), ['response' => 403]); }
        if (!current_user_can('manage_options')) { wp_die(__('You do not have sufficient permissions to export assets.', 'asset-manager'), __('Error', 'asset-manager'), ['response' => 403]); }
        
        $mpdf_autoloader = plugin_dir_path(__FILE__) . 'vendor/autoload.php';
        if (file_exists($mpdf_autoloader) && !class_exists('\Mpdf\Mpdf')) { 
            require_once $mpdf_autoloader;
        }
        if (!class_exists('\Mpdf\Mpdf')) { 
            wp_die(__('PDF Export library (mPDF) is missing or could not be loaded. Please ensure it is installed in the plugin\'s vendor directory.', 'asset-manager'), __('PDF Library Error', 'asset-manager'), ['back_link' => true]); return; 
        }
        
        $assets_query = new WP_Query(['post_type' => ASSET_MANAGER_POST_TYPE, 'posts_per_page' => -1, 'orderby' => 'title', 'order' => 'ASC']);
        $html = '<style> table { width: 100%; border-collapse: collapse; font-size: 10px; } th, td { border: 1px solid #ddd; padding: 6px; text-align: left; vertical-align: top; } th { background-color: #f2f2f2; } </style>';
        $html .= '<h1>' . esc_html__('Asset List', 'asset-manager') . '</h1>'; 
        // Added Location header and Date Purchased
        $html .= '<table><thead><tr><th>' . esc_html__('Title', 'asset-manager') . '</th><th>' . esc_html__('Asset Tag', 'asset-manager') . '</th><th>' . esc_html__('Model', 'asset-manager') . '</th><th>' . esc_html__('Serial No.', 'asset-manager') . '</th><th>' . esc_html__('Brand', 'asset-manager') . '</th><th>' . esc_html__('Category', 'asset-manager') . '</th><th>' . esc_html__('Location', 'asset-manager') . '</th><th>' . esc_html__('Status', 'asset-manager') . '</th><th>' . esc_html__('Issued To', 'asset-manager') . '</th><th>' . esc_html__('Date Purchased', 'asset-manager') . '</th><th>' . esc_html__('Description', 'asset-manager') . '</th></tr></thead><tbody>';
        
        if ($assets_query->have_posts()) {
            while ($assets_query->have_posts()) {
                $assets_query->the_post(); $post_id = get_the_ID();
                $meta_values = [];
                // Added 'location' and 'date_purchased' to keys for PDF
                $asset_meta_keys_for_pdf = [
                    'asset_tag', 'model', 'serial_number', 'brand', 
                    'status', 'issued_to', 'description', 'location', 'date_purchased'
                ];
                foreach ($asset_meta_keys_for_pdf as $field_key) { 
                     $meta_values[$field_key] = get_post_meta($post_id, ASSET_MANAGER_META_PREFIX . $field_key, true); 
                }

                $issued_to_name = '—'; 
                if (!empty($meta_values['issued_to'])) { 
                    $user = get_userdata($meta_values['issued_to']); 
                    $issued_to_name = $user ? $user->display_name : __('Unknown User', 'asset-manager'); 
                } else {
                    if ($meta_values['status'] === 'Unassigned') {
                        $issued_to_name = __('Unassigned', 'asset-manager');
                    }
                }
                $categories = get_the_terms($post_id, ASSET_MANAGER_TAXONOMY); $category_name = (!empty($categories) && !is_wp_error($categories)) ? esc_html(implode(', ', wp_list_pluck($categories, 'name'))) : '—';
                $date_purchased_formatted = $meta_values['date_purchased'] ? date_i18n(get_option('date_format'), strtotime($meta_values['date_purchased'])) : '—';
                // Added location and date purchased data cell
                $html .= '<tr><td>' . esc_html(get_the_title()) . '</td><td>' . esc_html($meta_values['asset_tag']) . '</td><td>' . esc_html($meta_values['model']) . '</td><td>' . esc_html($meta_values['serial_number']) . '</td><td>' . esc_html($meta_values['brand']) . '</td><td>' . $category_name . '</td><td>' . esc_html($meta_values['location']) . '</td><td>' . esc_html($meta_values['status']) . '</td><td>' . esc_html($issued_to_name) . '</td><td>' . esc_html($date_purchased_formatted) . '</td><td>' . nl2br(esc_html($meta_values['description'])) . '</td></tr>';
            } wp_reset_postdata();
        } else { $html .= '<tr><td colspan="11">' . esc_html__('No assets found.', 'asset-manager') . '</td></tr>'; } // Colspan updated to 11
        $html .= '</tbody></table>'; 
        try { $mpdf = new \Mpdf\Mpdf(['mode' => 'utf-8', 'format' => 'A4-L']); $mpdf->SetTitle(esc_attr__('Asset List', 'asset-manager')); $mpdf->SetAuthor(esc_attr(get_bloginfo('name'))); $mpdf->WriteHTML($html); $mpdf->Output('assets-' . date('Y-m-d') . '.pdf', 'D'); exit; } catch (\Mpdf\MpdfException $e) { wp_die(sprintf(esc_html__('Error generating PDF: %s', 'asset-manager'), esc_html($e->getMessage())), esc_html__('PDF Generation Error', 'asset-manager'), ['back_link' => true]); }
    }

    public function render_dashboard_page() { 
        ?> <div class="wrap asset-manager-dashboard"> <h1><?php esc_html_e('Asset Dashboard', 'asset-manager'); ?></h1> <div class="dashboard-widgets-wrapper"> <div class="dashboard-widget"><h2><?php esc_html_e('Assets by Status', 'asset-manager'); ?></h2><div class="chart-container"><canvas id="assetStatusChart"></canvas></div></div> <div class="dashboard-widget"><h2><?php esc_html_e('Assets by User', 'asset-manager'); ?></h2><div class="chart-container"><canvas id="assetUserChart"></canvas></div></div> <div class="dashboard-widget"><h2><?php esc_html_e('Assets by Category', 'asset-manager'); ?></h2><div class="chart-container"><canvas id="assetCategoryChart"></canvas></div></div> </div> </div> <?php
    }

    public function get_dashboard_data() {
        $status_data = []; $user_data = []; $category_data_counts = [];
        // Note: Location data is not added to the dashboard in this modification.
        // If you want charts by location, you would need to add logic here similar to status, user, and category.
        
        foreach ($this->status_options as $status_opt) {
            $status_data[$status_opt] = 0;
        }
        $status_data[__('Unknown', 'asset-manager')] = 0; 

        $all_categories = get_terms(['taxonomy' => ASSET_MANAGER_TAXONOMY, 'hide_empty' => false]);
        if (is_array($all_categories)) {
            foreach ($all_categories as $cat_term) {
                if (is_object($cat_term) && property_exists($cat_term, 'name')) {
                    $category_data_counts[esc_html($cat_term->name)] = 0;
                }
            }
        }
        $category_data_counts[__('Uncategorized', 'asset-manager')] = 0;
        $user_data[__('Unassigned', 'asset-manager')] = 0; 

        $assets_query = new WP_Query(['post_type' => ASSET_MANAGER_POST_TYPE, 'posts_per_page' => -1]);

        if ($assets_query->have_posts()) {
            while ($assets_query->have_posts()) {
                $assets_query->the_post();
                $post_id = get_the_ID();

                // Status
                $status_val = get_post_meta($post_id, ASSET_MANAGER_META_PREFIX . 'status', true);
                $display_status = '';
                if (empty($status_val)) { 
                    // If status meta is empty, but we have a default "Unassigned"
                    $display_status = 'Unassigned'; 
                } elseif (in_array($status_val, $this->status_options, true)) {
                    $display_status = $status_val;
                } else { 
                    $display_status = __('Unknown', 'asset-manager');
                }
                if (!isset($status_data[$display_status])) {
                     $status_data[$display_status] = 0; 
                }
                $status_data[$display_status]++;


                // User
                $user_id = get_post_meta($post_id, ASSET_MANAGER_META_PREFIX . 'issued_to', true);
                $current_asset_status = get_post_meta($post_id, ASSET_MANAGER_META_PREFIX . 'status', true);
                $user_name_key = __('Unassigned', 'asset-manager');

                if ($user_id) { 
                    $user = get_userdata($user_id);
                    $user_name_key = $user ? esc_html($user->display_name) : sprintf(__('Unknown User (ID: %d)', 'asset-manager'), $user_id);
                } elseif ($current_asset_status !== 'Unassigned' && empty($user_id)) {
                    // If not explicitly unassigned status, but no user, count as 'Needs Assignment' or similar for clarity
                    // For simplicity here, we'll still use Unassigned or make a new category like 'Needs User Assignment'
                     $user_name_key = __('Needs User (Not Unassigned Status)', 'asset-manager'); // Or handle as per requirements
                }
                // Ensure the key exists before incrementing
                if (!isset($user_data[$user_name_key])) { 
                    $user_data[$user_name_key] = 0;
                }
                $user_data[$user_name_key]++;

                // Category
                $terms = get_the_terms($post_id, ASSET_MANAGER_TAXONOMY);
                $category_name_key = __('Uncategorized', 'asset-manager');
                if (!empty($terms) && !is_wp_error($terms) && isset($terms[0]->name)) {
                     $category_name_key = esc_html($terms[0]->name);
                }
                if (!isset($category_data_counts[$category_name_key])) { 
                     $category_data_counts[$category_name_key] = 0;
                }
                $category_data_counts[$category_name_key]++;
            }
            wp_reset_postdata();
        }
        return [
            'status' => array_filter($status_data, function($count){ return $count >= 0; }), // Keep zero counts for all defined statuses
            'users' => array_filter($user_data, function($count){ return $count > 0; }),
            'categories' => array_filter($category_data_counts, function($count){ return $count > 0; })
        ];
    }

    public function register_shortcodes() { /* Placeholder */ }

    /**
     * Adds Category and Brand filters to the Asset list table.
     */
    public function add_asset_filters_to_admin_list() {
        global $typenow;

        if ($typenow == ASSET_MANAGER_POST_TYPE) {
            // Category Filter
            $selected_category = isset($_GET['asset_category_filter']) ? sanitize_text_field($_GET['asset_category_filter']) : '';
            wp_dropdown_categories([
                'show_option_all' => __('All Categories', 'asset-manager'),
                'taxonomy'        => ASSET_MANAGER_TAXONOMY,
                'name'            => 'asset_category_filter',
                'orderby'         => 'name',
                'selected'        => $selected_category,
                'hierarchical'    => true,
                'depth'           => 3,
                'show_count'      => true,
                'hide_empty'      => true,
                'value_field'     => 'slug',
            ]);

            // Brand Filter
            global $wpdb;
            $meta_key = ASSET_MANAGER_META_PREFIX . 'brand';
            // phpcs:ignore WordPress.DB.DirectDatabaseQuery.DirectQuery, WordPress.DB.DirectDatabaseQuery.NoCaching
            $brands = $wpdb->get_col($wpdb->prepare(
                "SELECT DISTINCT meta_value FROM $wpdb->postmeta WHERE meta_key = %s ORDER BY meta_value ASC",
                $meta_key
            ));

            $selected_brand = isset($_GET['asset_brand_filter']) ? sanitize_text_field($_GET['asset_brand_filter']) : '';
            if (!empty($brands)) {
                echo "<select name='asset_brand_filter' id='asset_brand_filter'>";
                echo "<option value=''>" . esc_html__('All Brands', 'asset-manager') . "</option>";
                foreach ($brands as $brand) {
                    if (empty($brand)) continue;
                    printf(
                        "<option value='%s'%s>%s</option>",
                        esc_attr($brand),
                        selected($selected_brand, $brand, false),
                        esc_html($brand)
                    );
                }
                echo "</select>";
            }
        }
    }

    /**
     * Modifies the main query based on selected filters.
     */
    public function filter_assets_query($query) {
        global $pagenow;
        $post_type = isset($_GET['post_type']) ? sanitize_text_field($_GET['post_type']) : '';

        if (is_admin() && $pagenow == 'edit.php' && $post_type == ASSET_MANAGER_POST_TYPE && $query->is_main_query()) {
            $meta_query_arr = $query->get('meta_query') ?: [];
            if (!is_array($meta_query_arr)) { // Ensure it's an array
                 $meta_query_arr = [];
            }


            // Category Filter
            if (isset($_GET['asset_category_filter']) && !empty($_GET['asset_category_filter'])) {
                $category_slug = sanitize_text_field($_GET['asset_category_filter']);
                $tax_query = $query->get('tax_query') ?: [];
                 if (!is_array($tax_query)) {
                    $tax_query = [];
                }
                $tax_query[] = [
                    'taxonomy' => ASSET_MANAGER_TAXONOMY,
                    'field'    => 'slug',
                    'terms'    => $category_slug,
                ];
                $query->set('tax_query', $tax_query);
            }

            // Brand Filter
            if (isset($_GET['asset_brand_filter']) && !empty($_GET['asset_brand_filter'])) {
                $brand_name = sanitize_text_field($_GET['asset_brand_filter']);
                $meta_query_arr[] = [
                    'key'     => ASSET_MANAGER_META_PREFIX . 'brand',
                    'value'   => $brand_name,
                    'compare' => '=',
                ];
            }
            
            if (!empty($meta_query_arr)) {
                 if (count($meta_query_arr) > 1 && !isset($meta_query_arr['relation'])) {
                     $meta_query_arr['relation'] = 'AND'; // Default relation for multiple filter conditions
                 }
                 $query->set('meta_query', $meta_query_arr);
            }
        }
    }

    /**
     * Extends the search functionality for assets.
     */
    public function extend_asset_search_query($query) {
        global $pagenow, $wpdb;
        $post_type = $query->get('post_type');
        $search_term = $query->get('s');

        // Ensure it's the main query, on the edit.php admin page, for our CPT, and a search is being performed.
        if (is_admin() && $query->is_main_query() && $pagenow === 'edit.php' && $post_type === ASSET_MANAGER_POST_TYPE && !empty($search_term)) {
            
            // Meta keys to search (excluding description, issued_to for direct meta search here)
            // issued_to would require searching user names then mapping to IDs - more complex for this direct meta search.
            // description is usually longer, title search is often enough.
            $meta_keys_to_search = [
                ASSET_MANAGER_META_PREFIX . 'asset_tag',
                ASSET_MANAGER_META_PREFIX . 'model',
                ASSET_MANAGER_META_PREFIX . 'serial_number',
                ASSET_MANAGER_META_PREFIX . 'brand',
                ASSET_MANAGER_META_PREFIX . 'location',
                ASSET_MANAGER_META_PREFIX . 'status',
                ASSET_MANAGER_META_PREFIX . 'date_purchased', // Simple LIKE search for date
            ];

            $search_meta_query = ['relation' => 'OR'];
            foreach ($meta_keys_to_search as $meta_key) {
                $search_meta_query[] = [
                    'key'     => $meta_key,
                    'value'   => $search_term,
                    'compare' => 'LIKE',
                ];
            }

            // To make the search work for title OR meta fields, we need a more complex approach
            // than just setting meta_query, as that typically ANDs with the title search.
            // We will use the 'posts_search' filter to modify the WHERE clause.

            // Store the meta query args for use in the posts_search filter
            // This is a bit of a workaround to pass data to the posts_search filter
            // A cleaner way might involve a dedicated class property if this gets more complex.
            $query->set('asset_manager_search_meta_query_args', $search_meta_query);

            add_filter('posts_search', [$this, 'asset_search_where_clause'], 10, 2);
            // We also need to join postmeta table
            add_filter('posts_join', [$this, 'asset_search_join_clause'], 10, 2);
            add_filter('posts_distinct', [$this, 'asset_search_distinct_clause'], 10, 2);


            // Search by Category Name
            // Find terms matching the search query
            $matching_terms = get_terms([
                'taxonomy'   => ASSET_MANAGER_TAXONOMY,
                'name__like' => $search_term,
                'fields'     => 'ids',
                'hide_empty' => false,
            ]);

            // Search by Issued To (User Display Name)
            $user_query_args = [
                'search'         => '*' . esc_attr($search_term) . '*',
                'search_columns' => ['user_login', 'user_nicename', 'user_email', 'display_name'],
                'fields'         => 'ID',
            ];
            $matching_user_ids = get_users($user_query_args);


            // Combine existing meta_query with search-specific meta_query
            $current_meta_query = $query->get('meta_query');
            if (!is_array($current_meta_query)) $current_meta_query = [];


            $overall_meta_query = $current_meta_query; // Keep existing filters (like brand filter)
            
            $additional_or_conditions = ['relation' => 'OR'];
            
            // Add condition for matching our specific meta keys
             $additional_or_conditions[] = $search_meta_query;


            if (!empty($matching_terms) && is_array($matching_terms)) {
                 $query->set('asset_manager_search_term_ids', $matching_terms);
                // The actual tax_query for search will be handled in posts_search for OR condition
            }
            if (!empty($matching_user_ids) && is_array($matching_user_ids)) {
                 $query->set('asset_manager_search_user_ids', $matching_user_ids);
                // The actual meta_query for user search will be handled in posts_search for OR condition
            }
             // Remove the 's' parameter to prevent default title/content search if we handle it all in posts_search
             // $query->set('s', ''); // This allows full control via posts_search
        }
    }

    public function asset_search_join_clause($join, $query) {
        global $wpdb;
        if (is_admin() && $query->is_main_query() && $query->get('asset_manager_search_meta_query_args')) {
            // Ensure postmeta is joined if not already
            if (strpos($join, $wpdb->postmeta) === false) {
                $join .= " LEFT JOIN $wpdb->postmeta ON ($wpdb->posts.ID = $wpdb->postmeta.post_id) ";
            }
            // Ensure term_relationships and term_taxonomy are joined for category search
            if ($query->get('asset_manager_search_term_ids')) {
                if (strpos($join, $wpdb->term_relationships) === false) {
                    $join .= " LEFT JOIN $wpdb->term_relationships ON ($wpdb->posts.ID = $wpdb->term_relationships.object_id) ";
                }
                if (strpos($join, $wpdb->term_taxonomy) === false) {
                     $join .= " LEFT JOIN $wpdb->term_taxonomy ON ($wpdb->term_relationships.term_taxonomy_id = $wpdb->term_taxonomy.term_taxonomy_id) ";
                }
                 if (strpos($join, $wpdb->terms) === false) {
                    $join .= " LEFT JOIN $wpdb->terms ON ($wpdb->term_taxonomy.term_id = $wpdb->terms.term_id) ";
                }
            }
        }
        return $join;
    }
    
    public function asset_search_distinct_clause($distinct, $query) {
         if (is_admin() && $query->is_main_query() && ($query->get('asset_manager_search_meta_query_args') || $query->get('asset_manager_search_term_ids'))) {
            return 'DISTINCT';
        }
        return $distinct;
    }


    public function asset_search_where_clause($where, $query) {
        global $wpdb;
        $search_term = $query->get('s');

        if (is_admin() && $query->is_main_query() && !empty($search_term)) {
            $meta_query_args = $query->get('asset_manager_search_meta_query_args');
            $term_ids_to_search = $query->get('asset_manager_search_term_ids');
            $user_ids_to_search = $query->get('asset_manager_search_user_ids');

            if ($meta_query_args || $term_ids_to_search || $user_ids_to_search) {
                $search_conditions = [];

                // Keep original title/content search
                $title_search = $wpdb->prepare("($wpdb->posts.post_title LIKE %s)", '%' . $wpdb->esc_like($search_term) . '%');
                 // $content_search = $wpdb->prepare("($wpdb->posts.post_content LIKE %s)", '%' . $wpdb->esc_like($search_term) . '%');
                 // $search_conditions[] = "($title_search OR $content_search)";
                 $search_conditions[] = $title_search;


                // Add meta field searches
                if ($meta_query_args && isset($meta_query_args['relation']) && $meta_query_args['relation'] === 'OR') {
                    $meta_sub_conditions = [];
                    foreach ($meta_query_args as $arg) {
                        if (is_array($arg) && isset($arg['key']) && isset($arg['value'])) {
                            // Ensure the meta key is one of the specific keys we want to search
                            $allowed_meta_keys = [
                                ASSET_MANAGER_META_PREFIX . 'asset_tag', ASSET_MANAGER_META_PREFIX . 'model', 
                                ASSET_MANAGER_META_PREFIX . 'serial_number', ASSET_MANAGER_META_PREFIX . 'brand', 
                                ASSET_MANAGER_META_PREFIX . 'location', ASSET_MANAGER_META_PREFIX . 'status',
                                ASSET_MANAGER_META_PREFIX . 'date_purchased'
                            ];
                            if (in_array($arg['key'], $allowed_meta_keys)) {
                                $meta_sub_conditions[] = $wpdb->prepare(
                                    "($wpdb->postmeta.meta_key = %s AND $wpdb->postmeta.meta_value LIKE %s)",
                                    $arg['key'],
                                    '%' . $wpdb->esc_like($arg['value']) . '%'
                                );
                            }
                        }
                    }
                    if (!empty($meta_sub_conditions)) {
                        $search_conditions[] = "(" . implode(' OR ', $meta_sub_conditions) . ")";
                    }
                }

                // Add category name search
                if (!empty($term_ids_to_search)) {
                     $search_conditions[] = $wpdb->prepare(
                        "($wpdb->term_taxonomy.taxonomy = %s AND $wpdb->terms.term_id IN (" . implode(',', array_map('intval', $term_ids_to_search)) . "))",
                        ASSET_MANAGER_TAXONOMY
                    );
                }
                
                // Add issued_to (user) search
                if (!empty($user_ids_to_search)) {
                     $search_conditions[] = $wpdb->prepare(
                        "($wpdb->postmeta.meta_key = %s AND $wpdb->postmeta.meta_value IN (" . implode(',', array_map('intval', $user_ids_to_search)) . "))",
                        ASSET_MANAGER_META_PREFIX . 'issued_to'
                    );
                }


                if (!empty($search_conditions)) {
                    // Replace the original search clause with our combined OR conditions
                    $where = " AND (" . implode(' OR ', $search_conditions) . ")";
                    
                    // If there were other meta queries from filters (e.g. brand filter), they need to be ANDed.
                    // This is complex to merge here. The pre_get_posts approach for filters is generally better.
                    // For simplicity, this override might affect pre-set meta_queries from filters if not handled carefully.
                    // The current filter_assets_query runs on pre_get_posts and sets up meta_query.
                    // This posts_search runs later. We need to ensure they combine correctly.
                    // One way is to let filter_assets_query build its part, and then this appends the search conditions.

                    // Let's try to preserve existing where clauses not related to the 's' parameter.
                    // This is tricky because the original $where from WP search includes the title/content search.
                    // A simple "OR" of everything can lead to too many results if filters are also active.
                    // We need the filters (brand, category dropdown) to be ANDed with the result of the broad search.

                    // The query structure should be: (Title LIKE %s% OR Meta1 LIKE %s% OR CatName LIKE %s% OR UserName LIKE %s%) AND (FilterBrand = X) AND (FilterCategory = Y)
                    // The default $where generated by WP for 's' is like: AND (((wp_posts.post_title LIKE %s%))))
                    // We are replacing this part.
                }
            }
             // Remove the filter after use to avoid affecting other queries
            remove_filter('posts_search', [$this, 'asset_search_where_clause'], 10, 2);
            remove_filter('posts_join', [$this, 'asset_search_join_clause'], 10, 2);
            remove_filter('posts_distinct', [$this, 'asset_search_distinct_clause'], 10, 2);

        }
        return $where;
    }


} // End Class Asset_Manager

new Asset_Manager();
