# Pattern Catalogs

Hardcoded pattern lists used as fallback when WebFetch is
unavailable. These catalogs are passed to Phase 3 agents.

## Fowler PoEAA (Patterns of Enterprise Application Architecture)

Source: https://martinfowler.com/eaaCatalog/

### Domain Logic Patterns
- Transaction Script
- Domain Model
- Table Module
- Service Layer

### Data Source Architectural Patterns
- Table Data Gateway
- Row Data Gateway
- Active Record
- Data Mapper

### Object-Relational Behavioral Patterns
- Unit of Work
- Identity Map
- Lazy Load

### Object-Relational Structural Patterns
- Identity Field
- Foreign Key Mapping
- Association Table Mapping
- Dependent Mapping
- Embedded Value
- Serialized LOB
- Single Table Inheritance
- Class Table Inheritance
- Concrete Table Inheritance
- Inheritance Mappers

### Object-Relational Metadata Mapping Patterns
- Metadata Mapping
- Query Object
- Repository

### Web Presentation Patterns
- Model View Controller
- Page Controller
- Front Controller
- Template View
- Transform View
- Two Step View
- Application Controller

### Distribution Patterns
- Remote Facade
- Data Transfer Object

### Offline Concurrency Patterns
- Optimistic Offline Lock
- Pessimistic Offline Lock
- Coarse-Grained Lock
- Implicit Lock

### Session State Patterns
- Client Session State
- Server Session State
- Database Session State

### Base Patterns
- Gateway
- Mapper
- Layer Supertype
- Separated Interface
- Registry
- Value Object
- Money
- Special Case
- Plugin
- Service Stub
- Record Set

## Refactoring Guru Design Patterns

Source: https://refactoring.guru/design-patterns/catalog

### Creational
- Factory Method
- Abstract Factory
- Builder
- Prototype
- Singleton

### Structural
- Adapter
- Bridge
- Composite
- Decorator
- Facade
- Flyweight
- Proxy

### Behavioral
- Chain of Responsibility
- Command
- Iterator
- Mediator
- Memento
- Observer
- State
- Strategy
- Template Method
- Visitor

## Software Archetypes

Source: https://www.softwarearchetypes.com/

### Core Archetypes
- **Catalog/Inventory** — manages collections of items with
  search, browse, filter. Examples: product catalog, service
  menu, parts inventory.
- **Document/Record** — creates, stores, retrieves structured
  documents. Examples: invoices, work orders, contracts.
- **Transaction/Event** — records and processes business events.
  Examples: payments, shipments, status changes.
- **Party/Role** — models people and organizations with their
  roles. Examples: customers, dealers, employees.
- **Place/Location** — represents physical or logical locations.
  Examples: stores, warehouses, service areas.
- **Thing/Item** — individual trackable items. Examples: tires,
  vehicles, equipment.
- **Quantity/Measurement** — measures and units. Examples: prices,
  weights, dimensions, tire sizes.
- **Rule/Policy** — encapsulates business rules and policies.
  Examples: pricing rules, tax rules, discount policies.

### Framework-Specific Pattern Focus

**Django projects — prioritize:**
- Repository vs Active Record usage
- Service Layer vs fat models
- Unit of Work (transaction.atomic patterns)
- Domain Model health (anemic vs rich)
- Value Object candidates (model fields with validators)

**React/Next.js projects — prioritize:**
- Component composition (Composite, Decorator)
- State management patterns (Observer, Mediator)
- Data fetching patterns (Repository, Gateway)
- Error boundary patterns (Chain of Responsibility)

**Go projects — prioritize:**
- Interface segregation (Separated Interface)
- Functional options (Builder variant)
- Middleware chains (Chain of Responsibility)
- Repository implementations
