## Table `django_migrations`

### Columns

| Name | Type | Constraints |
|------|------|-------------|
| `id` | `int8` | Primary Identity |
| `app` | `varchar` |  |
| `name` | `varchar` |  |
| `applied` | `timestamptz` |  |

## Table `django_content_type`

### Columns

| Name | Type | Constraints |
|------|------|-------------|
| `id` | `int4` | Primary Identity |
| `app_label` | `varchar` |  |
| `model` | `varchar` |  |

## Table `auth_permission`

### Columns

| Name | Type | Constraints |
|------|------|-------------|
| `id` | `int4` | Primary Identity |
| `name` | `varchar` |  |
| `content_type_id` | `int4` |  |
| `codename` | `varchar` |  |

## Table `auth_group`

### Columns

| Name | Type | Constraints |
|------|------|-------------|
| `id` | `int4` | Primary Identity |
| `name` | `varchar` |  Unique |

## Table `auth_group_permissions`

### Columns

| Name | Type | Constraints |
|------|------|-------------|
| `id` | `int8` | Primary Identity |
| `group_id` | `int4` |  |
| `permission_id` | `int4` |  |

## Table `auth_user`

### Columns

| Name | Type | Constraints |
|------|------|-------------|
| `id` | `int4` | Primary Identity |
| `password` | `varchar` |  |
| `last_login` | `timestamptz` |  Nullable |
| `is_superuser` | `bool` |  |
| `username` | `varchar` |  Unique |
| `first_name` | `varchar` |  |
| `last_name` | `varchar` |  |
| `email` | `varchar` |  |
| `is_staff` | `bool` |  |
| `is_active` | `bool` |  |
| `date_joined` | `timestamptz` |  |

## Table `auth_user_groups`

### Columns

| Name | Type | Constraints |
|------|------|-------------|
| `id` | `int8` | Primary Identity |
| `user_id` | `int4` |  |
| `group_id` | `int4` |  |

## Table `auth_user_user_permissions`

### Columns

| Name | Type | Constraints |
|------|------|-------------|
| `id` | `int8` | Primary Identity |
| `user_id` | `int4` |  |
| `permission_id` | `int4` |  |

## Table `django_admin_log`

### Columns

| Name | Type | Constraints |
|------|------|-------------|
| `id` | `int4` | Primary Identity |
| `action_time` | `timestamptz` |  |
| `object_id` | `text` |  Nullable |
| `object_repr` | `varchar` |  |
| `action_flag` | `int2` |  |
| `change_message` | `text` |  |
| `content_type_id` | `int4` |  Nullable |
| `user_id` | `int4` |  |

## Table `marriage_users`

### Columns

| Name | Type | Constraints |
|------|------|-------------|
| `id` | `int8` | Primary Identity |
| `firstName` | `varchar` |  |
| `middleName` | `varchar` |  Nullable |
| `lastName` | `varchar` |  |
| `mobile` | `varchar` |  Unique |
| `email` | `varchar` |  Unique |
| `password` | `varchar` |  |
| `is_active` | `bool` |  |
| `name` | `varchar` |  Nullable |

## Table `templates`

### Columns

| Name | Type | Constraints |
|------|------|-------------|
| `id` | `int8` | Primary Identity |
| `deleted_at` | `timestamptz` |  Nullable |
| `created_at` | `timestamptz` |  |
| `updated_at` | `timestamptz` |  |
| `name` | `varchar` |  Unique |
| `display_name` | `varchar` |  |
| `description` | `text` |  Nullable |
| `thumbnail` | `varchar` |  Nullable |
| `is_active` | `bool` |  |
| `created_by_id` | `int8` |  Nullable |
| `deleted_by_id` | `int8` |  Nullable |
| `updated_by_id` | `int8` |  Nullable |

## Table `categories`

### Columns

| Name | Type | Constraints |
|------|------|-------------|
| `id` | `int8` | Primary Identity |
| `is_active` | `bool` |  |
| `created_at` | `timestamptz` |  |
| `updated_at` | `timestamptz` |  |
| `deleted_at` | `timestamptz` |  Nullable |
| `name` | `varchar` |  Unique |
| `created_by_id` | `int4` |  Nullable |
| `deleted_by_id` | `int4` |  Nullable |
| `updated_by_id` | `int4` |  Nullable |

## Table `customers`

### Columns

| Name | Type | Constraints |
|------|------|-------------|
| `id` | `int8` | Primary Identity |
| `is_active` | `bool` |  |
| `created_at` | `timestamptz` |  |
| `updated_at` | `timestamptz` |  |
| `deleted_at` | `timestamptz` |  Nullable |
| `name` | `varchar` |  |
| `address` | `text` |  |
| `state` | `varchar` |  |
| `pincode` | `varchar` |  Nullable |
| `phone` | `varchar` |  Nullable |
| `email` | `varchar` |  Nullable |
| `created_by_id` | `int4` |  Nullable |
| `deleted_by_id` | `int4` |  Nullable |
| `updated_by_id` | `int4` |  Nullable |

## Table `platforms`

### Columns

| Name | Type | Constraints |
|------|------|-------------|
| `id` | `int8` | Primary Identity |
| `is_active` | `bool` |  |
| `created_at` | `timestamptz` |  |
| `updated_at` | `timestamptz` |  |
| `deleted_at` | `timestamptz` |  Nullable |
| `name` | `varchar` |  Unique |
| `code` | `varchar` |  Unique |
| `created_by_id` | `int4` |  Nullable |
| `deleted_by_id` | `int4` |  Nullable |
| `updated_by_id` | `int4` |  Nullable |

## Table `marketplace_orders`

### Columns

| Name | Type | Constraints |
|------|------|-------------|
| `id` | `int8` | Primary Identity |
| `is_active` | `bool` |  |
| `created_at` | `timestamptz` |  |
| `updated_at` | `timestamptz` |  |
| `deleted_at` | `timestamptz` |  Nullable |
| `marketplace_order_id` | `varchar` |  |
| `order_date` | `date` |  |
| `created_by_id` | `int4` |  Nullable |
| `customer_id` | `int8` |  |
| `deleted_by_id` | `int4` |  Nullable |
| `platform_id` | `int8` |  |
| `updated_by_id` | `int4` |  Nullable |

## Table `biodata`

### Columns

| Name | Type | Constraints |
|------|------|-------------|
| `id` | `int8` | Primary Identity |
| `is_active` | `bool` |  |
| `deleted_at` | `timestamptz` |  Nullable |
| `created_at` | `timestamptz` |  |
| `updated_at` | `timestamptz` |  |
| `data` | `jsonb` |  |
| `photo` | `varchar` |  Nullable |
| `created_by_id` | `int8` |  Nullable |
| `deleted_by_id` | `int8` |  Nullable |
| `template_id` | `int8` |  Nullable |
| `updated_by_id` | `int8` |  Nullable |
| `marriage_user_id` | `int8` |  |

## Table `products`

### Columns

| Name | Type | Constraints |
|------|------|-------------|
| `id` | `int8` | Primary Identity |
| `is_active` | `bool` |  |
| `created_at` | `timestamptz` |  |
| `updated_at` | `timestamptz` |  |
| `deleted_at` | `timestamptz` |  Nullable |
| `catalog_id` | `varchar` |  Unique |
| `name` | `varchar` |  |
| `category_id` | `int8` |  |
| `created_by_id` | `int4` |  Nullable |
| `deleted_by_id` | `int4` |  Nullable |
| `owner_id` | `int4` |  |
| `updated_by_id` | `int4` |  Nullable |
| `commission_percent` | `numeric` |  |
| `gst_percent` | `numeric` |  |
| `platform_id` | `int8` |  |

## Table `product_variants`

### Columns

| Name | Type | Constraints |
|------|------|-------------|
| `id` | `int8` | Primary Identity |
| `sku` | `varchar` |  |
| `size` | `varchar` |  Nullable |
| `color` | `varchar` |  Nullable |
| `cost_price` | `float8` |  |
| `selling_price` | `float8` |  |
| `stock` | `int4` |  |
| `product_id` | `int8` |  |
| `rto_cost` | `float8` |  |
| `shipping_cost` | `float8` |  |

## Table `order_status`

### Columns

| Name | Type | Constraints |
|------|------|-------------|
| `id` | `int8` | Primary Identity |
| `is_active` | `bool` |  |
| `created_at` | `timestamptz` |  |
| `updated_at` | `timestamptz` |  |
| `deleted_at` | `timestamptz` |  Nullable |
| `code` | `varchar` |  Unique |
| `label` | `varchar` |  |
| `created_by_id` | `int4` |  Nullable |
| `deleted_by_id` | `int4` |  Nullable |
| `updated_by_id` | `int4` |  Nullable |

## Table `orders`

### Columns

| Name | Type | Constraints |
|------|------|-------------|
| `id` | `int8` | Primary Identity |
| `is_active` | `bool` |  |
| `created_at` | `timestamptz` |  |
| `updated_at` | `timestamptz` |  |
| `deleted_at` | `timestamptz` |  Nullable |
| `marketplace_sub_order_id` | `varchar` |  |
| `quantity` | `int4` |  |
| `selling_price` | `float8` |  |
| `created_by_id` | `int4` |  Nullable |
| `deleted_by_id` | `int4` |  Nullable |
| `marketplace_order_id` | `int8` |  |
| `product_id` | `int8` |  |
| `status_id` | `int8` |  |
| `updated_by_id` | `int4` |  Nullable |
| `status_updated_at` | `timestamptz` |  Nullable |
| `variant_id` | `int8` |  |
| `delivery_partner_id` | `int8` |  Nullable |
| `payment_type` | `varchar` |  |

## Table `order_settlements`

### Columns

| Name | Type | Constraints |
|------|------|-------------|
| `id` | `int8` | Primary Identity |
| `is_active` | `bool` |  |
| `created_at` | `timestamptz` |  |
| `updated_at` | `timestamptz` |  |
| `deleted_at` | `timestamptz` |  Nullable |
| `transaction_id` | `varchar` |  |
| `payment_date` | `date` |  |
| `total_sale_amount` | `float8` |  |
| `total_return_amount` | `float8` |  |
| `final_settlement_amount` | `float8` |  |
| `fixed_fee` | `float8` |  |
| `warehousing_fee` | `float8` |  |
| `return_premium` | `float8` |  |
| `return_premium_return` | `float8` |  |
| `gst_percent` | `numeric` |  |
| `created_by_id` | `int4` |  Nullable |
| `deleted_by_id` | `int4` |  Nullable |
| `order_id` | `int8` |  |
| `updated_by_id` | `int4` |  Nullable |
| `platform_id` | `int8` |  Nullable |
| `extra_data` | `jsonb` |  Nullable |
| `claim_amount` | `float8` |  |
| `commission_fee` | `float8` |  |
| `is_claim` | `bool` |  |
| `is_return` | `bool` |  |
| `is_rto` | `bool` |  |
| `return_shipping_charge` | `float8` |  |
| `shipping_fee` | `float8` |  |

## Table `django_session`

### Columns

| Name | Type | Constraints |
|------|------|-------------|
| `session_key` | `varchar` | Primary |
| `session_data` | `text` |  |
| `expire_date` | `timestamptz` |  |

## Table `user_profile`

### Columns

| Name | Type | Constraints |
|------|------|-------------|
| `id` | `int8` | Primary Identity |
| `first_name` | `varchar` |  Nullable |
| `last_name` | `varchar` |  Nullable |
| `mobile_number` | `varchar` |  Nullable |
| `email` | `varchar` |  Nullable |
| `is_active` | `bool` |  |
| `created_at` | `timestamptz` |  |
| `trial_start` | `timestamptz` |  Nullable |
| `trial_end` | `timestamptz` |  Nullable |
| `subscription_start` | `timestamptz` |  Nullable |
| `subscription_end` | `timestamptz` |  Nullable |
| `payment_verified` | `bool` |  |
| `user_id` | `int4` |  Unique |

## Table `delivery_partners`

### Columns

| Name | Type | Constraints |
|------|------|-------------|
| `id` | `int8` | Primary Identity |
| `is_active` | `bool` |  |
| `created_at` | `timestamptz` |  |
| `updated_at` | `timestamptz` |  |
| `deleted_at` | `timestamptz` |  Nullable |
| `name` | `varchar` |  Unique |
| `code` | `varchar` |  Unique |
| `created_by_id` | `int4` |  Nullable |
| `deleted_by_id` | `int4` |  Nullable |
| `updated_by_id` | `int4` |  Nullable |

## Table `notifications`

### Columns

| Name | Type | Constraints |
|------|------|-------------|
| `id` | `int8` | Primary Identity |
| `is_active` | `bool` |  |
| `created_at` | `timestamptz` |  |
| `updated_at` | `timestamptz` |  |
| `deleted_at` | `timestamptz` |  Nullable |
| `type` | `varchar` |  |
| `title` | `varchar` |  |
| `message` | `text` |  |
| `priority` | `varchar` |  |
| `is_read` | `bool` |  |
| `data` | `jsonb` |  Nullable |
| `order_id` | `int8` |  Nullable |
| `product_id` | `int8` |  Nullable |
| `user_id` | `int4` |  |
| `created_by_id` | `int4` |  Nullable |
| `deleted_by_id` | `int4` |  Nullable |
| `updated_by_id` | `int4` |  Nullable |

## Table `cost_price_update_history`

### Columns

| Name | Type | Constraints |
|------|------|-------------|
| `id` | `int8` | Primary Identity |
| `is_active` | `bool` |  |
| `created_at` | `timestamptz` |  |
| `updated_at` | `timestamptz` |  |
| `deleted_at` | `timestamptz` |  Nullable |
| `old_cost_price` | `float8` |  |
| `new_cost_price` | `float8` |  |
| `created_by_id` | `int4` |  Nullable |
| `deleted_by_id` | `int4` |  Nullable |
| `updated_by_id` | `int4` |  Nullable |
| `variant_id` | `int8` |  |

## Table `ai_chat_history`

### Columns

| Name | Type | Constraints |
|------|------|-------------|
| `id` | `int8` | Primary Identity |
| `is_active` | `bool` |  |
| `created_at` | `timestamptz` |  |
| `updated_at` | `timestamptz` |  |
| `deleted_at` | `timestamptz` |  Nullable |
| `platform` | `varchar` |  Nullable |
| `intent` | `varchar` |  |
| `user_message` | `text` |  |
| `assistant_reply` | `text` |  |
| `analytics_summary` | `jsonb` |  Nullable |
| `metadata` | `jsonb` |  Nullable |
| `created_by_id` | `int4` |  Nullable |
| `deleted_by_id` | `int4` |  Nullable |
| `updated_by_id` | `int4` |  Nullable |
| `user_id` | `int4` |  |

## Table `account_locks`

### Columns

| Name | Type | Constraints |
|------|------|-------------|
| `id` | `int8` | Primary Identity |
| `locked_at` | `timestamptz` |  |
| `locked_until` | `timestamptz` |  |
| `failed_attempts` | `int4` |  |
| `last_failed_attempt` | `timestamptz` |  Nullable |
| `reason` | `varchar` |  |
| `user_id` | `int4` |  Unique |

## Table `login_attempts`

### Columns

| Name | Type | Constraints |
|------|------|-------------|
| `id` | `int8` | Primary Identity |
| `email` | `varchar` |  |
| `ip_address` | `inet` |  |
| `user_agent` | `text` |  Nullable |
| `success` | `bool` |  |
| `reason` | `varchar` |  |
| `created_at` | `timestamptz` |  |
| `user_id` | `int4` |  Nullable |

## Table `refresh_tokens`

### Columns

| Name | Type | Constraints |
|------|------|-------------|
| `id` | `int8` | Primary Identity |
| `token_hash` | `varchar` |  Unique |
| `revoked_at` | `timestamptz` |  Nullable |
| `expires_at` | `timestamptz` |  |
| `created_at` | `timestamptz` |  |
| `updated_at` | `timestamptz` |  |
| `ip_address` | `inet` |  Nullable |
| `user_agent` | `text` |  Nullable |
| `device_id` | `varchar` |  Nullable |
| `is_active` | `bool` |  |
| `user_id` | `int4` |  |

## Table `session_logs`

### Columns

| Name | Type | Constraints |
|------|------|-------------|
| `id` | `int8` | Primary Identity |
| `event_type` | `varchar` |  |
| `ip_address` | `inet` |  |
| `user_agent` | `text` |  Nullable |
| `device_id` | `varchar` |  Nullable |
| `status` | `varchar` |  |
| `details` | `jsonb` |  |
| `created_at` | `timestamptz` |  |
| `user_id` | `int4` |  |

## Table `token_blacklist`

### Columns

| Name | Type | Constraints |
|------|------|-------------|
| `id` | `int8` | Primary Identity |
| `token_hash` | `varchar` |  Unique |
| `reason` | `varchar` |  |
| `created_at` | `timestamptz` |  |
| `expires_at` | `timestamptz` |  |
| `user_id` | `int4` |  |

## Table `captcha_challenges`

### Columns

| Name | Type | Constraints |
|------|------|-------------|
| `challenge_id` | `uuid` | Primary |
| `code_hash` | `varchar` |  |
| `created_at` | `timestamptz` |  |
| `expires_at` | `timestamptz` |  |
| `ip_address` | `inet` |  Nullable |
| `attempts` | `int4` |  |
| `verified` | `bool` |  |
| `used` | `bool` |  |

## Table `order_profit`

### Columns

| Name | Type | Constraints |
|------|------|-------------|
| `id` | `int8` | Primary Identity |
| `is_active` | `bool` |  |
| `created_at` | `timestamptz` |  |
| `updated_at` | `timestamptz` |  |
| `deleted_at` | `timestamptz` |  Nullable |
| `product_name` | `varchar` |  |
| `sku` | `varchar` |  |
| `quantity` | `int4` |  |
| `selling_price` | `numeric` |  |
| `gross_revenue` | `numeric` |  |
| `product_cost` | `numeric` |  |
| `shipping_cost` | `numeric` |  |
| `rto_cost` | `numeric` |  |
| `packaging_cost` | `numeric` |  |
| `commission_fee` | `numeric` |  |
| `fixed_fee` | `numeric` |  |
| `warehousing_fee` | `numeric` |  |
| `return_shipping_charge` | `numeric` |  |
| `total_return_amount` | `numeric` |  |
| `claim_amount` | `numeric` |  |
| `total_cost` | `numeric` |  |
| `total_deductions` | `numeric` |  |
| `net_profit` | `numeric` |  |
| `profit_margin_percent` | `numeric` |  |
| `roi_percent` | `numeric` |  |
| `is_loss` | `bool` |  |
| `created_by_id` | `int4` |  Nullable |
| `deleted_by_id` | `int4` |  Nullable |
| `order_id` | `int8` |  Unique |
| `settlement_id` | `int8` |  Nullable |
| `updated_by_id` | `int4` |  Nullable |

