# PyPongAI - Final Research Extensions Implementation Plan

## Overview
Two major research extensions to push PyPongAI to cutting-edge research status:
1. **Remove Speed Cap** - Allow unlimited ball velocity for high-performance training
2. **Four-Corner Pong** - Multi-agent 4-paddle variant for advanced spatial reasoning

---

## EXTENSION 1: Remove Speed Cap

### Current Limitations
**Speed caps found:**
- `config.py` line 17: `BALL_MAX_SPEED = 15`
- `game_simulator.py` lines 285-286: Velocity clamping
- `game_engine.py` lines 105-106: Velocity clamping

### Implementation Steps

**Step 1: Increase BALL_MAX_SPEED in config.py**
```python
# Change from:
BALL_MAX_SPEED = 15

# To:
BALL_MAX_SPEED = 100  # Allow much higher speeds for advanced AI
```

**Step 2: Remove velocity clamping in game_simulator.py (lines 285-286)**
```python
# REMOVE these lines:
self.ball.vel_x = max(min(self.ball.vel_x, config.BALL_MAX_SPEED), -config.BALL_MAX_SPEED)
self.ball.vel_y = max(min(self.ball.vel_y, config.BALL_MAX_SPEED), -config.BALL_MAX_SPEED)

# OR make it optional:
if config.ENABLE_SPEED_CAP:
    self.ball.vel_x = max(min(self.ball.vel_x, config.BALL_MAX_SPEED), -config.BALL_MAX_SPEED)
    self.ball.vel_y = max(min(self.ball.vel_y, config.BALL_MAX_SPEED), -config.BALL_MAX_SPEED)
```

**Step 3: Same for game_engine.py (lines 105-106)**
Apply same change as Step 2.

**Step 4: Add config option**
```python
# In config.py, add:
ENABLE_SPEED_CAP = False  # Set to False for unlimited speed
BALL_MAX_SPEED = 100  # Only used if ENABLE_SPEED_CAP is True
```

### Benefits
- AI can learn to handle extreme velocities
- More challenging training scenarios
- Better generalization to high-speed gameplay
- Identifies true performance limits

---

## EXTENSION 2: Four-Corner Pong

### Architecture Overview

**Current:**  
- 2 paddles (left, right)
- 8 inputs per AI

**Proposed:**
- 4 paddles (left, right, top, bottom)
- Each AI controls 1 paddle
- Expanded input vector (12-16 inputs)
- Multi-agent competitive environment

### Game Engine Modifications

#### **Paddle Representation**
```python
# In game_simulator.py / game_engine.py

class FourCornerGameSimulator:
    def __init__(self):
        # Existing
        self.paddle_left = Paddle(10, SCREEN_HEIGHT // 2 - PADDLE_HEIGHT // 2)
        self.paddle_right = Paddle(SCREEN_WIDTH - 10 - PADDLE_WIDTH, 
                                    SCREEN_HEIGHT // 2 - PADDLE_HEIGHT // 2)
        
        # NEW: Top and bottom paddles (horizontal orientation)
        self.paddle_top = PaddleHorizontal(SCREEN_WIDTH // 2 - PADDLE_WIDTH // 2, 10)
        self.paddle_bottom = PaddleHorizontal(SCREEN_WIDTH // 2 - PADDLE_WIDTH // 2,
                                               SCREEN_HEIGHT - 10 - PADDLE_HEIGHT)
```

#### **New Paddle Class**
```python
class PaddleHorizontal:
    """Horizontal paddle for top/bottom positions."""
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.width = PADDLE_HEIGHT  # Swap dimensions
        self.height = PADDLE_WIDTH
        self.vel_x = 0  # Moves left-right instead of up-down
    
    def move(self, direction):
        if direction == "LEFT":
            self.vel_x = -PADDLE_MAX_SPEED
        elif direction == "RIGHT":
            self.vel_x = PADDLE_MAX_SPEED
        else:
            self.vel_x = 0
    
    def update(self):
        self.x += self.vel_x
        # Boundary check
        if self.x < 0:
            self.x = 0
        if self.x + self.width > SCREEN_WIDTH:
            self.x = SCREEN_WIDTH - self.width
```

#### **Collision Detection**
```python
def check_collisions(self):
    # Existing left/right checks
    if self.ball.x <= self.paddle_left.x + self.paddle_left.width:
        if (self.paddle_left.y <= self.ball.y <= 
            self.paddle_left.y + self.paddle_left.height):
            self.ball.vel_x = abs(self.ball.vel_x) * 1.05
            # Contact metrics...
            return {"hit_left": True, ...}
    
    # NEW: Top paddle collision
    if self.ball.y <= self.paddle_top.y + self.paddle_top.height:
        if (self.paddle_top.x <= self.ball.x <= 
            self.paddle_top.x + self.paddle_top.width):
            self.ball.vel_y = abs(self.ball.vel_y) * 1.05
            return {"hit_top": True, ...}
    
    # NEW: Bottom paddle collision
    if self.ball.y + self.ball.size >= self.paddle_bottom.y:
        if (self.paddle_bottom.x <= self.ball.x <= 
            self.paddle_bottom.x + self.paddle_bottom.width):
            self.ball.vel_y = -abs(self.ball.vel_y) * 1.05
            return {"hit_bottom": True, ...}
```

#### **Scoring System**
```python
def check_scoring(self):
    # Left side scores (right player missed)
    if self.ball.x + self.ball.size >= SCREEN_WIDTH:
        return {"scored": "left"}
    
    # Right side scores (left player missed)
    if self.ball.x <= 0:
        return {"scored": "right"}
    
    # NEW: Top scores (bottom player missed)
    if self.ball.y + self.ball.size >= SCREEN_HEIGHT:
        return {"scored": "top"}
    
    # NEW: Bottom scores (top player missed)
    if self.ball.y <= 0:
        return {"scored": "bottom"}
    
    return None
```

### AI Input Vector Expansion

**Current (8 inputs):**
1. paddle_y (normalized)
2. ball_x
3. ball_y
4. ball_vel_x
5. ball_vel_y
6. relative_y (paddle - ball)
7. incoming_flag (vel_x direction)
8. opponent_paddle_y

**Proposed (16 inputs for each AI):**
```python
def get_state_for_paddle(self, paddle_id):
    """Returns state from perspective of one paddle.
    
    Args:
        paddle_id: "left", "right", "top", or "bottom"
    """
    base_inputs = [
        self.ball.x / SCREEN_WIDTH,
        self.ball.y / SCREEN_HEIGHT,
        self.ball.vel_x / BALL_MAX_SPEED,
        self.ball.vel_y / BALL_MAX_SPEED,
    ]
    
    if paddle_id == "left":
        specific_inputs = [
            self.paddle_left.y / SCREEN_HEIGHT,
            (self.paddle_left.y - self.ball.y) / SCREEN_HEIGHT,
            1.0 if self.ball.vel_x < 0 else 0.0,  # incoming
            self.paddle_right.y / SCREEN_HEIGHT,
            self.paddle_top.x / SCREEN_WIDTH,
            self.paddle_bottom.x / SCREEN_WIDTH,
        ]
    elif paddle_id == "top":
        specific_inputs = [
            self.paddle_top.x / SCREEN_WIDTH,
            (self.paddle_top.x - self.ball.x) / SCREEN_WIDTH,
            1.0 if self.ball.vel_y < 0 else 0.0,  # incoming
            self.paddle_bottom.x / SCREEN_WIDTH,
            self.paddle_left.y / SCREEN_HEIGHT,
            self.paddle_right.y / SCREEN_HEIGHT,
        ]
    # Similar for "right" and "bottom"
    
    return base_inputs + specific_inputs
```

### Training Configuration

#### **NEAT Config Updates**
```ini
# neat_config_4corner.txt
[DefaultGenome]
num_inputs              = 10  # Simplified: ball position/velocity + own paddle + 3 opponents
num_outputs             = 3   # STAY, LEFT/UP, RIGHT/DOWN (direction depends on paddle orientation)
```

#### **Multi-Agent Evaluation**
```python
def eval_genomes_four_corner(genomes, config_neat):
    """4-paddle competitive evaluation."""
    genome_list = list(genomes)
    
    # Initialize ELO
    for _, genome in genome_list:
        if not hasattr(genome, 'elo_rating'):
            genome.elo_rating = config.ELO_INITIAL_RATING
    
    # Each genome plays as each paddle position
    for idx, (genome_id, genome) in enumerate(genome_list):
        # Create 4 networks (for 4-way matches)
        opponents = random.sample([g for g in genome_list if g[0] != genome_id], 3)
        
        nets = {
            "left": neat.nn.RecurrentNetwork.create(genome, config_neat),
            "right": neat.nn.RecurrentNetwork.create(opponents[0][1], config_neat),
            "top": neat.nn.RecurrentNetwork.create(opponents[1][1], config_neat),
            "bottom": neat.nn.RecurrentNetwork.create(opponents[2][1], config_neat)
        }
        
        for net in nets.values():
            net.reset()
        
        game = FourCornerGameSimulator()
        
        # Game loop
        while run:
            # Get actions from all 4 AIs
            for paddle_id, net in nets.items():
                inputs = game.get_state_for_paddle(paddle_id)
                output = net.activate(inputs)
                action = get_action_from_output(output, paddle_id)
                moves[paddle_id] = action
            
            # Update game with 4 moves
            score_data = game.update(moves["left"], moves["right"], 
                                     moves["top"], moves["bottom"])
            
            # Update ELO based on who scored
            # 4-way ELO: winner gains from 3 losers
```

### Visual Rendering

```python
def draw(self, screen):
    screen.fill(BLACK)
    
    # Existing left/right paddles
    pygame.draw.rect(screen, WHITE, self.paddle_left.get_rect())
    pygame.draw.rect(screen, WHITE, self.paddle_right.get_rect())
    
    # NEW: Top/bottom paddles
    pygame.draw.rect(screen, WHITE, self.paddle_top.get_rect())
    pygame.draw.rect(screen, WHITE, self.paddle_bottom.get_rect())
    
    # Ball
    pygame.draw.circle(screen, WHITE, (int(self.ball.x), int(self.ball.y)), 
                      self.ball.size)
    
    # Score (4-way)
    score_text = f"L:{self.score_left} R:{self.score_right} T:{self.score_top} B:{self.score_bottom}"
    # ... render text
```

---

## Implementation Priority

### Phase 1: Speed Cap Removal (15 min)
1. Update `config.py` - increase BALL_MAX_SPEED
2. Comment out velocity clamping in `game_simulator.py`
3. Comment out velocity clamping in `game_engine.py`
4. Test with `python main.py`

### Phase 2: Four-Corner Foundation (1-2 hours)
1. Create `game_simulator_4corner.py` with new classes
2. Implement horizontal paddle movement
3. Add 4-way collision detection
4. Test collisions independently

### Phase 3: Four-Corner AI Integration (1-2 hours)
1. Create `ai_module_4corner.py` with multi-agent evaluation
2. Update input vector for 4 perspectives
3. Implement 4-way ELO system
4. Create `neat_config_4corner.txt`

### Phase 4: UI Integration (30 min)
1. Add "Four-Corner Mode" button to menu
2. Create `states/four_corner_train.py`
3. Visual rendering for 4 paddles

---

## Research Value

### Speed Cap Removal
- Tests AI limits in extreme conditions
- Reveals whether current architectures can scale
- Publishable results on velocity generalization

### Four-Corner Pong
- **Multi-agent learning**: 4-way competition
- **Spatial complexity**: 360-degree awareness required
- **Novel research**: No existing NEAT-based 4-paddle pong in literature
- **Scalability test**: Can RNNs handle increased complexity?

### Potential Papers
1. "Unlimited Velocity Generalization in Neural Pong Agents"
2. "Four-Corner Pong: Multi-Agent Spatial Reasoning with NEAT"
3. "From 2D to 4D: Scaling Neuroevolution in Bounded Environments"

---

## Files to Create/Modify

### New Files
- `game_simulator_4corner.py` - 4-paddle game engine
- `ai_module_4corner.py` - Multi-agent training
- `neat_config_4corner.txt` - 10-16 input config
- `states/four_corner_train.py` - Training UI
- `FOUR_CORNER_RESEARCH.md` - Documentation

### Modified Files
- `config.py` - Add ENABLE_SPEED_CAP, increase BALL_MAX_SPEED
- `game_simulator.py` - Optional speed capping
- `game_engine.py` - Optional speed capping
- `states/menu.py` - Add "Four-Corner Mode" button
- `main.py` - Register four-corner state

---

## Success Criteria

### Speed Cap Removal
✅ Ball exceeds 15 units/frame
✅ AI successfully tracks high-speed balls
✅ No crashes or instability
✅ ELO continues to increase

### Four-Corner Pong
✅ All 4 paddles move independently
✅ Ball bounces correctly off all 4 walls + 4 paddles
✅ Scoring works for all 4 sides
✅ 4-way ELO system converges
✅ Multi-agent training completes 50 generations
✅ Visual mode displays all 4 paddles correctly

The PyPongAI platform will be a one-of-a-kind research tool! 🚀🔬
