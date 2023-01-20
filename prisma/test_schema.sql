CREATE TABLE admin_users (
    id bigint NOT NULL,
    email character varying NOT NULL, -- choices: "karen@witharsenal.com", "ryan@witharsenal.com", "callie@witharsenal.com", "allie@witharsenal.com", "ben@witharsenal.com", "tyler@witharsenal.com", "omar@witharsenal.com", "matt@witharsenal.com", "corey@witharsenal.com", "katieh@witharsenal.com", "nate@witharsenal.com", "phillip@witharsenal.com", "carol@witharsenal.com", "andrew@witharsenal.com", "joew@witharsenal.com"
    password_digest character varying NOT NULL, -- choices: "$2a$10$DsY.7n.N56CoEiOl3fiK1.9X1rCzjAkgLcmQ6UDMdout/PsurPyMi", "$2a$10$p6xXVWEvwo4lhe0Rs3DjG.0xwMTgWT1b/c/1UMyWJ/pk08Bumx5XS", "$2a$10$FzIP9srBOQrQbMoUUo0EdO0yJscbpy3Ea.y4kQF/bEWi28dKzkTSK", "$2a$10$qhdV1HVCCAt9jHJ1W5EX3OLSGFhWirPl9zRcA/Sdkir8M0jWogVPy", "$2a$10$FUArZ.dXsrlhTBu48M.n3uA63j72GVk4AuV9jKQB1rOxSdHUV64hK", "$2a$10$X2gSSnYx4LZtEfxAL/dehey.CF19ruOWfw20Nii69WV6dDHwG5Kge", "$2a$10$d1niPTM01WAY/mWzwkaAquAlc032xKXdnQVviqCkPejKALMKarfRa", "$2a$10$/yfrY9NUY3heDp4DGwZvEubl7HmsjytqMtgZAa/9yfxfVx3mcObmq", "$2a$10$Rr1SQTb7CC5Pur6MVDycuu0YSvWHmILzwKvcTqMvH0i3l13srXoKa", "$2a$10$UZWgA.7QLg2y5eCfxKPvvOh9SqyTzYxIS9DtiG01ishiyGZK31MyG", "$2a$10$b4vNvrK7PR1puHIDFhuf8uBa3LOHo5cnx64BSeoiQjHu0s8Nb48Om", "$2a$10$5CT/qpN/YxgNR4lIGYMkZeTWCJQmpzpSIV1IK/P60.xyKGYDO2aUy", "$2a$10$fl0iDzjr2y9GukRcGiw4h.sJMPO.YlNPzA2fQ0BHICbCCct2HpYYa", "$2a$10$gOtLEEtYosj93pinFjSS9ujP7otYHcTz29rZAEhkA6Xngdu/EU4n.", "$2a$10$Z24MHiijr8/.V2wyfpc4BOjaqXs1RxXvGcAjtr7wREJyOR7ssO4um"
    permissions json NOT NULL,
    failed_login_attempts integer DEFAULT 0 NOT NULL,
    reset_token character varying, -- choices: null
    created_at timestamp without time zone NOT NULL,
    updated_at timestamp without time zone NOT NULL
);
CREATE TABLE entries (
    id bigint NOT NULL,
    order_id bigint NOT NULL,
    created_at timestamp without time zone NOT NULL,
    updated_at timestamp without time zone NOT NULL
);
CREATE TABLE line_items (
    id bigint NOT NULL,
    product_id bigint NOT NULL,
    order_id bigint NOT NULL,
    price_cents integer NOT NULL,
    quantity integer NOT NULL,
    metadata json,
    created_at timestamp without time zone NOT NULL,
    updated_at timestamp without time zone NOT NULL
);
CREATE TABLE ar_internal_metadata (
    key character varying NOT NULL, -- choices: "environment"
    value character varying, -- choices: "production"
    created_at timestamp without time zone NOT NULL,
    updated_at timestamp without time zone NOT NULL
);
CREATE TABLE bad_addresses (
    id bigint NOT NULL,
    name character varying,
    address_1 character varying,
    address_2 character varying,
    city character varying,
    country character varying, -- values include but are not limited to: "United States of America", "Hong Kong", "Thailand", "India", "United Kingdom of Great Britain and Northern Ireland", "Malaysia", "Philippines", "Korea (Republic of)", "Israel", "Canada", "Taiwan", "Puerto Rico", "Viet Nam", "Australia", "Turkey", "Ireland", "Argentina", "United Arab Emirates", "Chile", "Macao", "Germany", "Saudi Arabia", "Japan", "China", "Oman", "Mexico", "Pakistan", "Spain", "Bahrain", "Lebanon"...
    state character varying,
    zipcode character varying,
    created_at timestamp without time zone NOT NULL,
    updated_at timestamp without time zone NOT NULL,
    email character varying,
    ordered boolean DEFAULT false
);
CREATE TABLE entry_items (
    id bigint NOT NULL,
    entry_id bigint NOT NULL,
    line_item_id bigint NOT NULL,
    price_cents integer NOT NULL,
    quantity integer NOT NULL,
    quantity_delta integer NOT NULL,
    total_cents integer NOT NULL,
    delta_cents integer NOT NULL,
    created_at timestamp without time zone NOT NULL,
    updated_at timestamp without time zone NOT NULL
);
CREATE TABLE crowdox_order_confirmations (
    id bigint NOT NULL,
    crowdox_order_number character varying NOT NULL,
    confirm_hash character varying NOT NULL,
    confirmed_at timestamp without time zone
);
CREATE TABLE kickstarter_subscribers (
    id bigint NOT NULL,
    phone character varying, -- choices: null, "+15037806294"
    email character varying,
    created_at timestamp without time zone NOT NULL,
    updated_at timestamp without time zone NOT NULL,
    subscribed boolean DEFAULT true
);
CREATE TABLE charges (
    id bigint NOT NULL,
    order_id bigint NOT NULL,
    stripe_charge_id character varying,
    amount_cents integer NOT NULL,
    refunded_amount_cents integer NOT NULL,
    created_at timestamp without time zone NOT NULL,
    updated_at timestamp without time zone NOT NULL,
    source character varying DEFAULT 'witharsenal'::character varying -- choices: "witharsenal", "kickstarter"
);
CREATE TABLE amazon_fulfillment_shipments (
    id bigint NOT NULL,
    shipment_id bigint,
    amazon_shipment_id character varying,
    status character varying, -- choices: "SHIPPED", "PENDING", "CANCELLED_BY_SELLER"
    package_number character varying,
    carrier_code character varying, -- choices: "USPS", "UPS", null, "Amazon Logistics", "LASERSHIP", "BRING PickUp", "Post Danmark", "Oesterreichische Post AG", "Posti", "POLISH_POST_EU", "UPSM", "An Post", "La Poste", "Deutsche Post Brief", "BRING Home Delivery", "Colis Privé", "Airmee Same day", "HRVATSKA_POST", "SEUR", "ASM", "POST_NORD", "DPDDE", "FAN", "Poste Italiane", "SDA", "CTT_PT", "CORREOS", "DHL NL Pakketten", "DHL", "DHL_ES"
    tracking_number character varying,
    estimated_arrival_at timestamp without time zone,
    created_at timestamp without time zone NOT NULL,
    updated_at timestamp without time zone NOT NULL
);
CREATE TABLE amazon_fulfillment_logs (
    id bigint NOT NULL,
    shipment_id bigint,
    action character varying, -- choices: "refresh", "create", "cancel", "update"
    request_args text,
    response_xml text,
    created_at timestamp without time zone NOT NULL,
    updated_at timestamp without time zone NOT NULL
);
CREATE TABLE promo_codes (
    id bigint NOT NULL,
    active boolean DEFAULT true NOT NULL,
    email character varying,
    code character varying NOT NULL,
    discount_amount_cents integer,
    discount_percentage integer,
    one_time_use boolean DEFAULT true NOT NULL,
    used_at timestamp without time zone,
    created_at timestamp without time zone NOT NULL,
    updated_at timestamp without time zone NOT NULL
);
CREATE TABLE schema_migrations (
    version character varying NOT NULL -- values include but are not limited to: "20181119185519", "20220307205042", "20200703000244", "20180508011606", "20181119185030", "20170815142730", "20181119170804", "20180326155616", "20180405153102", "20170815004718", "20210824002624", "20171016174027", "20191028203545", "20170815142637", "20171215151227", "20200318235418", "20171218160814", "20180404140518", "20190307211738", "20180713193318", "20200813235646", "20181221143625", "20210126163900", "20191008231845", "20210913222642", "20201012175958", "20171009213332", "20180410062428", "20171207170723", "20171211221418"...
);
CREATE TABLE settings (
    id bigint NOT NULL,
    prevent_refunds_after_30_days boolean DEFAULT false NOT NULL,
    created_at timestamp without time zone NOT NULL,
    updated_at timestamp without time zone NOT NULL
);
CREATE TABLE products (
    id bigint NOT NULL,
    name character varying NOT NULL, -- choices: "Promo Code", "Sales Tax", "Shipping", "Partial Refund", "USB Micro 3.0 Cable for Arsenal 2 Pro", "USB Micro Cable", "Arsenal", "USB Mini Cable for Arsenal 2 Pro", "USB-C Cable for Arsenal 2 Pro", "USB Mini Cable (8 pin)", "Arsenal 2 Standard", "USB Mini Cable (8 pin) for Arsenal 1", "USB-C Cable for Arsenal 1", "Battery", "USB Micro Cable for Arsenal 1", "Arsenal 2 Pro", "USB Micro 3.0 Cable for Arsenal 1", "USB Micro 3.0 Cable", "Proprietary", "USB Mini Cable (8 pin) for Arsenal 2 Pro", "USB-C Cable", "USB Micro Cable for Arsenal 2 Pro", "USB Mini Cable", "Micro SD Card", "USB Mini Cable for Arsenal 1", "Phone Mount"
    price_cents integer NOT NULL,
    product_type character varying NOT NULL, -- choices: "Cable", "Arsenal", "Accessory", "Shipping", "Partial Refund", "Sales Tax", "Promo Code"
    created_at timestamp without time zone NOT NULL,
    updated_at timestamp without time zone NOT NULL,
    retail_price_cents integer,
    preorder boolean DEFAULT false,
    total_quantity_available integer,
    cached_quantity_ordered integer
);
CREATE TABLE shipment_imports (
    id bigint NOT NULL,
    csv_data text,
    status character varying, -- choices: "finished"
    result text,
    created_at timestamp without time zone NOT NULL,
    updated_at timestamp without time zone NOT NULL,
    fulfiller character varying -- choices: null, "kolibri", "amazon", "north_of_you", "floship"
);
CREATE TABLE shipping_methods (
    id bigint NOT NULL,
    name character varying NOT NULL, -- choices: "Standard Shipping", "Express Shipping", "Two Business Day Shipping"
    price_cents integer NOT NULL,
    min_delivery_days integer NOT NULL,
    max_delivery_days integer NOT NULL,
    country character varying NOT NULL,
    created_at timestamp without time zone NOT NULL,
    updated_at timestamp without time zone NOT NULL,
    notes character varying, -- choices: null, "Express orders cannot be shipped to P.O. boxes", "", "Two-day orders cannot be shipped to P.O. boxes"
    fulfiller character varying DEFAULT 'floship'::character varying, -- choices: "north_of_you", "floship", "amazon", "kolibri"
    speed character varying, -- choices: null, "Standard", "Priority", "Expedited"
    active boolean DEFAULT true
);
CREATE TABLE sms_replies (
    id bigint NOT NULL,
    from character varying, -- choices: "+15037806294", "+18032616150"
    message text,
    original_params text,
    created_at timestamp without time zone NOT NULL,
    updated_at timestamp without time zone NOT NULL
);
CREATE TABLE shipments (
    id bigint NOT NULL,
    order_id bigint NOT NULL,
    fulfiller character varying NOT NULL, -- choices: "old_floship", "north_of_you", "floship", "amazon", "kolibri"
    status character varying DEFAULT 'pending'::character varying NOT NULL, -- choices: "pending", "fulfilled", "canceled", "created", "failed_and_cleared", "failed", "shipped", "enqueued", "approved", "pending_fulfillment", "out_for_pick_pack", "incomplete"
    floship_order_id integer,
    error_message text,
    courier_name character varying, -- choices: null
    tracking_number character varying,
    tracking_url character varying,
    created_at timestamp without time zone NOT NULL,
    updated_at timestamp without time zone NOT NULL,
    import_id bigint,
    kolibri_order_id integer,
    amazon_order_id character varying
);

CREATE TABLE tax_reporting_logs (
    id bigint NOT NULL,
    operation character varying, -- choices: "create_order", "create_refund"
    payload text,
    success boolean DEFAULT true,
    error character varying, -- choices: null, "#<Taxjar::Error::NotAcceptable: to_state can't be blank>", "#<Taxjar::Error::NotAcceptable: to_zip can't be blank>"
    archived boolean DEFAULT false,
    created_at timestamp without time zone NOT NULL,
    updated_at timestamp without time zone NOT NULL,
    order_uid character varying
);
CREATE TABLE unsupported_camera_subscribers (
    id bigint NOT NULL,
    email character varying,
    camera_brand character varying, -- choices: "Sony", "Canon", "Olympus", "Nikon", "Fuji", "Other", "Panasonic", "Pentax", "Panasonic Lumix", "Leica", "Hasselblad", "Samsung", "Phase One", "Minolta", "Sigma", "Mamiya Leaf"
    camera_model character varying,
    created_at timestamp without time zone NOT NULL,
    updated_at timestamp without time zone NOT NULL,
    arsenal_version character varying -- choices: "2", "1"
);
CREATE TABLE vip_refunds (
    id uuid DEFAULT public.gen_random_uuid() NOT NULL,
    email character varying NOT NULL, -- values include but are not limited to: "hiroshi.komoda@gmail.com", "joe@santangeloco.net", "phcarroll@eircom.net", "j.w.p.king@gmail.com", "jspitzer@nvidia.com", "dhkellam@gmail.com", "anas@anasone.com", "leosmith@ku.edu", "holly@urbanucbranding.com", "jsschanche@gmail.com", "marklainsworth@gamil.com", "kris.permentier@telenet.be", "hotsouma@gmail.com", "hdeslandes@granadasolutions.com", "orders@dynot.com", "egnutz@aol.com", "staffan.bruzelius@gmail.com", "kenliew@me.com", "gll22@live.ca", "alexwang81@me.com", "yasuhiro-himeno@kccshokai.co.jp", "cbvine@gmail.com", "ouimetclaude4@gmail.com", "dustin.thompson.md@gmail.com", "ratyning@me.com", "sultanfsa@gmail.com", "michaelhoopes@gmail.com", "rachel@madisonstudio.com.au", "anthonyvpappas@gmail.com", "krwashington2@yahoo.com"...
    name character varying NOT NULL, -- values include but are not limited to: "Customer", "Paddy Carroll", "Dustin", "Rajesh NG", "Staffan Bruzelius", "michael warnecke", "Doug Brennecke", "Heather Clements", "Mohammed Abbas", "Kenneth Liew Jau Tze", "John Stevenson", "Philippe Page", "Chad Wilcox", "R Bob Smith III", "sultanfsa", "Jacob", "Mark Ainsworth", "Dennis Huey", "Brett Hershey", "baba", "Leo Smith", "Helder Mendes Martins", "Bryan Yoon", "weisspr", "DESLANDES", "Dieter Yih", "Michael Hoopes", "Bill Wagner", "Jon-Sverre Schanche", "Kirt Washington"...
    amount_cents integer NOT NULL,
    refund_type character varying, -- choices: null, "partial", "full"
    email_sent boolean DEFAULT false NOT NULL,
    created_at timestamp without time zone NOT NULL,
    updated_at timestamp without time zone NOT NULL,
    refunded boolean DEFAULT false NOT NULL
);
CREATE TABLE orders (
    id bigint NOT NULL,
    uid character varying NOT NULL,
    email character varying NOT NULL,
    stripe_customer_id character varying,
    shipping_name character varying NOT NULL, -- values include but are not limited to: "Nate Stephens", "Ryan Stout", "David", "Mark", "Michael", "John", "Robert", "Matt Fegel", "Peter", "Home", "Daniel", "Mike", "NATE STEPHENS", "Andrew", "Kevin", "James", "Jason", "Chris", "Robert Smith", "Alex", "Michael Smith", "Steve", "Paul", "Justin", "James Lee", "David Williams", "Jonathan", "David Jones", "Brandon", "Christopher"...
    shipping_address_1 character varying,
    shipping_address_2 character varying,
    shipping_city character varying,
    shipping_country character varying NOT NULL, -- choices: "United States of America", "Canada", "Australia", "United Kingdom of Great Britain and Northern Ireland", "Germany", "Switzerland", "Netherlands", "France", "Italy", "Singapore", "New Zealand", "Sweden", "Hong Kong", "Norway", "Belgium", "India", "Spain", "Denmark", "Austria", "Japan", "United Arab Emirates", "Israel", "Thailand", "Ireland", "Mexico", "Korea (Republic of)", "Taiwan", "Finland", "Malaysia", "Brazil", "Czech Republic", "Poland", "Russian Federation", "South Africa", "Portugal", "Philippines", "Indonesia", "Chile", "Iceland", "Luxembourg", "Hungary", "Romania", "Greece", "China", "Saudi Arabia", "Qatar", "Slovakia", "Puerto Rico", "Malta", "Viet Nam", "Slovenia", "Bulgaria", "Argentina", "Estonia", "Croatia", "Turkey", "Cyprus", "Latvia", "Oman", "Colombia", "Ukraine", "Kuwait", "Peru", "Macao", "Lithuania", "Jersey", "Lebanon", "Bahrain", "Pakistan", "Serbia", "Isle of Man", "New Caledonia", "Greenland", "Guernsey", "Cambodia", "Monaco", "Bermuda", "Guam", "Réunion", "Mauritius", "Liechtenstein", "Cayman Islands", "French Polynesia", "Sri Lanka", "Maldives", "Brunei Darussalam", "Ecuador", "Guadeloupe", "Kazakhstan", "Gibraltar", "Uruguay", "Faroe Islands", "Bosnia and Herzegovina", "Costa Rica", "Curaçao", "Nigeria", "Namibia", "Egypt", "Virgin Islands (U.S.)", "Jordan", "Bangladesh", "Martinique", "Aruba", "Macedonia (the former Yugoslav Republic of)", "Saint Martin (French part)", "Montenegro", "Bolivia (Plurinational State of)", "Panama", "French Guiana", "Seychelles", "Albania", "Angola", "Morocco", "Guatemala", "Madagascar", "Moldova (Republic of)", "Kenya", "Barbados", "Armenia", "Mongolia", "Andorra", "Trinidad and Tobago", "Algeria", "Lao People's Democratic Republic", "Åland Islands", "Ghana", "Micronesia (Federated States of)", "Norfolk Island", "Zambia", "Dominican Republic", "Saint Barthélemy", "American Samoa", "United States Minor Outlying Islands", "Georgia", "Northern Mariana Islands", "Paraguay", "Palestine, State of", "Kosovo, Republic of", "Falkland Islands (Malvinas)", "Ethiopia", "El Salvador", "Myanmar", "Saint Pierre and Miquelon", "Samoa", "San Marino", "Senegal", "Guyana", "Burkina Faso", "Botswana", "Honduras", "Suriname", "Svalbard and Jan Mayen", "Mayotte", "Tanzania, United Republic of", "Timor-Leste", "Togo", "Tunisia", "Turks and Caicos Islands", "Palau", "Uzbekistan"
    shipping_state character varying, -- values include but are not limited to: "California", "Texas", "Florida", "New York", "Washington", null, "Ontario", "Colorado", "Illinois", "Virginia", "Pennsylvania", "Arizona", "New Jersey", "Georgia", "New South Wales", "Michigan", "North Carolina", "Oregon", "Massachusetts", "Ohio", "Victoria", "Maryland", "British Columbia", "Utah", "Minnesota", "Queensland", "Tennessee", "Wisconsin", "Alberta", "Missouri"...
    shipping_zipcode character varying,
    card_exp_month integer,
    card_exp_year integer,
    card_last_4 character varying,
    card_brand character varying, -- choices: "Visa", "MasterCard", "American Express", null, "Discover", "JCB", "Diners Club"
    total_cents integer NOT NULL,
    created_at timestamp without time zone NOT NULL,
    updated_at timestamp without time zone NOT NULL,
    utm_data USER-DEFINED,
    phone_number character varying,
    estimated_delivery character varying NOT NULL,
    confirm_preorder_email_sent boolean DEFAULT false NOT NULL,
    dhl_tracking_number character varying, -- values include but are not limited to: null, "HKADJFS1535355", "HKADJFS1535489", "HKADJFS1535379", "HKADJFS1535383", "HKADJFS1535409", "HKADJFS1535449", "HKADJFS1535458", "HKADJFS1535466", "HKADJFS1535467A", "HKADJFS1535469", "HKADJFS1535475", "HKADJFS1535482", "HKADJFS1535486", "HKADJFS1535371", "HKADJFS1535503", "HKADJFS1535505", "HKADJFS1535515A", "HKADJFS1535522", "HKADJFS1535523", "HKADJFS1535526", "HKADJFS1535531", "HKADJFS1535567", "HKADJFS1535574", "HKADJFS1535588", "HKADJFS1535608", "HKADJFS1535613", "HKADJFS1535614A", "HKADJFS1535620", "HKADJFS1532745"...
    shipping_method_id bigint,
    preorder boolean DEFAULT true NOT NULL,
    promo_code_id bigint,
    original_estimated_delivery character varying,
    kickstarter_backer_uid character varying,
    imported_at timestamp without time zone,
    shipping_number character varying,
    shipping_extension character varying, -- values include but are not limited to: null, "", ".", "A", "B", "C", "1", "D", "F", "3", "2", "4", "E", "11", "a", "8", "13", "15", "A2", "10", "35", "G", "32", "30", "M", "28", "14", "6", "20", "19"...
    shipping_street character varying,
    shipping_street2 character varying
);