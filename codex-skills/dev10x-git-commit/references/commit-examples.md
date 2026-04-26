# Commit Message Examples

Real examples of well-formatted commit messages following project conventions.

## Test Improvements

### Example 1: Fixing Flaky Tests
```
✅ PAY-310 Fix flaky tests with non-zero tax amounts

Tests in TestAddTireServiceIndividual and TestAddTireServiceMultiple
were marked as flaky because they randomly failed when tax amounts
or percentages were generated as zero by Faker.

Solution:
- Added non_zero trait to MoneyFaker with min_value=Decimal('0.01')
- Updated test fixtures to ensure tax amounts and percentages >= 0.01
- Removed @pytest.mark.flaky decorators

Fixes: PAY-310
```

### Example 2: Adding Test Coverage
```
✅ PAY-289 Add tests for discount code validation

The discount validation logic had no test coverage, making it risky
to modify or refactor.

Solution:
- Created TestDiscountValidation test class with 8 test cases
- Added DiscountCodeFaker for test data generation
- Tests cover: expiry, usage limits, invalid codes, race conditions
- Achieved 100% coverage for validation module

Fixes: PAY-289
```

## Bug Fixes

### Example 3: Production Bug
```
🐛 PAY-133 Fix motor timeout in payment processing

MotorTimeoutException occurs when Square API is slow to respond,
causing checkout failures for customers. Timeout was set to 5s
which is too aggressive under load.

Solution:
- Increase Motor timeout from 5s to 15s for payment endpoints
- Add exponential backoff retry (3 attempts)
- Improve error logging with request context
- Add timeout metric to Sentry

Fixes: PAY-133
```

### Example 4: Data Integrity Bug
```
🐛 PAY-275 Fix tax calculation for exempt customers

Tax-exempt customers were incorrectly charged sales tax through
Square terminal checkout. The OrderConverter was not checking
customer tax exemption status when generating Square orders.

Solution:
- Update OrderConverter to accept tax_exemption parameter
- Read exemption from WorkOrderRepository.tax_exemption()
- Apply exemption in _get_taxes() method
- Add tests for all exemption scenarios

Fixes: PAY-275
```

## Refactoring

### Example 5: Extract to Base Class
```
♻️ PAY-200 Refactor payment repository to use base class

PaymentRepository duplicated CRUD operations that exist in
BaseRepository. This refactor reduces duplication and establishes
consistent repository patterns.

Solution:
- Update PaymentRepository to extend BaseRepository[PaymentDto]
- Remove duplicate get/create/update/delete methods
- Keep custom payment-specific queries
- Verify all tests still pass

Fixes: PAY-200
```

### Example 6: Service Extraction
```
♻️ PAY-180 Extract discount validation to service

Discount code validation logic was scattered across mutations
and repository. Extracting to DiscountService centralizes
business logic and improves testability.

Solution:
- Create DiscountService with validate_code() method
- Move validation logic from mutations to service
- Update DiscountRepository to focus on data access only
- Register DiscountService in DI container

Fixes: PAY-180
```

## New Features

### Example 7: Business Feature
```
✨ PAY-220 Add discount code system

Store managers need the ability to create promotional discount
codes that customers can apply during checkout. Codes can have
expiration dates and usage limits.

Solution:
- Create DiscountCode model with expiry and usage_limit fields
- Implement DiscountRepository for CRUD operations
- Add DiscountService for validation logic
- Create GraphQL mutations: createDiscountCode, applyDiscountCode
- Add discount application to payment calculator
- Write tests for validation edge cases

Fixes: PAY-220
```

### Example 8: API Enhancement
```
✨ PAY-195 Add pagination to customer search results

Customer search was returning all results causing slow performance
and poor UX with large datasets. Added cursor-based pagination
following GraphQL Relay specification.

Solution:
- Update CustomerSearchHandler to support pagination
- Implement cursor encoding/decoding for stable pagination
- Add first/after/last/before parameters to search query
- Include pageInfo in response with hasNextPage/hasPreviousPage
- Update tests for pagination scenarios

Fixes: PAY-195
```

## Performance Improvements

### Example 9: Database Optimization
```
⚡ PAY-211 Optimize search query with compound index

Customer search was taking 2-3 seconds due to full table scan.
Added compound index on (dealer_id, last_name, first_name) to
improve query performance.

Solution:
- Create migration with compound index on customers table
- Update search query to use index (ordering by indexed columns)
- Benchmark: Search time reduced from 2.3s to 180ms (12x faster)
- Add index maintenance notes to repository docstring

Fixes: PAY-211
```

### Example 10: Caching
```
⚡ PAY-156 Cache tax settings lookup per request

TaxSettings were loaded from database on every quote calculation,
causing 10-15 redundant queries per work order. Implemented
per-request caching to reduce database load.

Solution:
- Add cache dict to TaxSettingsRepository __init__
- Implement _get_cached() method with cache-aside pattern
- Clear cache between requests (request-scoped)
- Benchmark: Reduced queries from 15 to 1 per work order
- Database load reduced by 40% in production

Fixes: PAY-156
```

## Documentation

### Example 11: README Update
```
📝 Update README with Docker setup instructions

New developers were struggling with local setup using Docker.
Added comprehensive Docker setup instructions with common
troubleshooting steps.

Solution:
- Add Docker prerequisites section
- Document make services and make services-daemon commands
- Add troubleshooting section for common port conflicts
- Include database setup instructions for local development

Fixes: DOC-45
```

### Example 12: Architecture Decision Record
```
📝 Add ADR for payment retry strategy

Documented decision to use exponential backoff with jitter for
payment retries to prevent thundering herd problem when external
services recover.

Solution:
- Create ADR-012-payment-retry-strategy.md
- Document context, decision, and consequences
- Include retry timing diagram
- Reference relevant code locations

Fixes: DOC-52
```

## Security Fixes

### Example 13: Authorization Fix
```
🔒 PAY-240 Fix authorization check in discount mutations

Store managers from other dealers could create/modify discount
codes for any store due to missing dealer_id authorization check
in DiscountMutations.

Solution:
- Add dealer_id permission check in createDiscountCode mutation
- Add store ownership validation in updateDiscountCode mutation
- Add tests for cross-dealer authorization attempts
- Audit other mutations for similar issues (all OK)

Fixes: PAY-240
```

## Multiple Change Types

### Example 14: Bug Fix + Refactor
```
🐛 PAY-302 Fix race condition in payment processing

Duplicate payments were created when checkout was initiated twice
within 5 seconds. Fixed by adding idempotency key and refactored
payment creation to use select_for_update().

Solution:
- Add idempotency_key column to payments table
- Use idempotency key from Square API as unique constraint
- Refactor create_payment() to check existing payment first
- Add select_for_update() to prevent race conditions
- Add tests for concurrent checkout attempts

Fixes: PAY-302
```

### Example 15: Feature + Tests
```
✨ PAY-267 Add bulk discount code upload

Store managers can now upload multiple discount codes via CSV
file instead of creating them one by one. Includes validation
and error reporting for invalid rows.

Solution:
- Add uploadDiscountCodes GraphQL mutation with file upload
- Implement CSV parsing with validation (pandas)
- Return success/error counts with error details
- Add transaction rollback on validation failures
- Write integration tests for valid/invalid CSV scenarios
- Add CSV format documentation

Fixes: PAY-267
```

## Tips for Writing Good Commit Messages

1. **Title (First Line)**:
   - ≤ 72 characters
   - Imperative mood ("Fix", not "Fixed" or "Fixes")
   - Specific and clear

2. **Problem Explanation**:
   - What was wrong?
   - Why did it need fixing?
   - Who was affected?

3. **Solution Points**:
   - Bulleted list
   - Specific changes made
   - Include file names if relevant

4. **Footer**:
   - Always include `Fixes: TICKET-ID`
   - Links ticket to commit

5. **What NOT to Include**:
   - Co-authoring attribution to Claude
   - How long it took
   - Personal notes
   - Emoji in solution points (gitmoji in title only)
