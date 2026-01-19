#!/usr/bin/env node

/**
 * Encodes store HTML content to Base64 for obfuscation.
 * This prevents casual viewing of store content in page source.
 *
 * Note: This is security through obscurity, not true security.
 * The real security is the password protection. This just makes it
 * harder to casually view the content without entering the password.
 */

const fs = require('fs');
const path = require('path');

// The HTML content to encode (store section)
const storeContent = `<section id="Store" class="parallax">
    <div class="container">
        <div class="row-fluid">
            <div class="store-content span12">
                <div class="store-intro">
                    <p>Purchase prints or book a portrait session.</p>
                </div>

                <!-- Success Message -->
                <div id="success-message" class="success-banner" role="status" aria-live="polite" style="display: none;">
                    <p>Thank you for your purchase! You'll receive a confirmation email shortly.</p>
                </div>

                <div class="store-sections">
                    <!-- Prints Section -->
                    <div class="store-section">
                        <h3>Prints</h3>
                        <p class="section-description">High-quality prints of my photography, professionally printed on archival paper.</p>

                        <div class="product-grid" id="prints-grid">
                            <div class="loading-placeholder">Loading prints...</div>
                        </div>
                    </div>

                    <!-- Services Section -->
                    <div class="store-section">
                        <h3>Photography Services</h3>
                        <p class="section-description">Book a portrait session for professional headshots, family photos, or special occasions.</p>

                        <div class="services-grid" id="services-grid">
                            <div class="loading-placeholder">Loading services...</div>
                        </div>
                    </div>
                </div>

                <div class="store-outro">
                    <p><a href="/#Photography" class="back-link">&larr; Back</a></p>
                </div>
            </div>
        </div>
    </div>
</section>`;

// Encode to Base64
const encoded = Buffer.from(storeContent).toString('base64');

// Output as JSON string for webpack
console.log(JSON.stringify(encoded));
