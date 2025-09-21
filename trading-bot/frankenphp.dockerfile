# Ultra-minimal FrankenPHP production image
FROM dunglas/frankenphp:alpine AS base

# Set environment variables
ENV COMPOSER_ALLOW_SUPERUSER=1
ENV COMPOSER_NO_INTERACTION=1
ENV COMPOSER_NO_AUDIT=1

# Install only essential runtime dependencies
RUN apk add --no-cache \
    curl \
    && rm -rf /var/cache/apk/*

# Install minimal PHP extensions needed for trading bot
RUN install-php-extensions \
    opcache \
    bcmath \
    curl \
    json \
    mbstring \
    zip \
    gmp

# Install Composer
RUN curl -sS https://getcomposer.org/installer | php -- --install-dir=/usr/local/bin --filename=composer \
    && composer --version

# Production stage - ultra-minimal
FROM base AS production

# Set working directory
WORKDIR /app

# Copy only essential files for dependency installation
COPY composer.json composer.lock ./

# Install dependencies with minimal footprint
RUN composer install --no-dev --optimize-autoloader --no-scripts --no-cache \
    && composer clear-cache \
    && rm -rf /root/.composer

# Copy application files (exclude unnecessary files)
COPY src/ ./src/
COPY public/ ./public/
COPY bin/ ./bin/
COPY .env* ./

# Create minimal directory structure
RUN mkdir -p storage/logs \
    && chown -R www-data:www-data storage bin \
    && chmod +x bin/console \
    && find . -name "*.log" -delete 2>/dev/null || true \
    && find . -name "*.tmp" -delete 2>/dev/null || true

# Create production .env if missing
RUN if [ ! -f .env ]; then \
    echo "# Kraken Trading Bot Production Environment" > .env && \
    echo "APP_ENV=production" >> .env && \
    echo "APP_DEBUG=false" >> .env && \
    echo "LOG_LEVEL=info" >> .env; \
    fi

# Final cleanup - remove all unnecessary files
RUN rm -rf /tmp/* /var/tmp/* /var/cache/* \
    && find /var/log -type f -delete 2>/dev/null || true \
    && find . -name "*.md" -delete 2>/dev/null || true \
    && find . -name "*.txt" -delete 2>/dev/null || true \
    && find . -name ".*" -type f -delete 2>/dev/null || true

# Expose ports
EXPOSE 80 443

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD curl -f http://localhost/health || exit 1

# Default command
CMD ["frankenphp", "run", "--config", "/etc/caddy/Caddyfile"]