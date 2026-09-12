# Mirror Runtime

Mirror is the human-facing interface to HumanOS. It coordinates context, model inference, governed capabilities, and durable output while preserving human control.

## Responsibilities

- Present the current session and recovery state
- Route bounded local queries without unnecessary model calls
- Provide selected context within explicit budgets
- Request authorization for governed actions
- Surface uncertainty and failures rather than silently retrying consequential work
- Preserve final responses before emission

## Non-responsibilities

Mirror does not own the human's decisions, silently broaden permissions, treat model reasoning as verified evidence, or claim receipt merely because bytes were written to an output stream.

Runtime 0.1 uses a terminal interface. Graphical interfaces and external service bridges are future integration layers, not prerequisites for the core architecture.
