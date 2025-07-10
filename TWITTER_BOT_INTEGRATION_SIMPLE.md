# Simple Integration Guide for Your Existing Twitter Bot

## What to Do

1. **Copy the file**: Copy `simple_game_state.js` to your Twitter bot directory (`/Users/lucasimonetti/Work/uomi-rival-bot/`)

2. **Add one line to your existing bot**: At the top of your bot file, add:
```javascript
const { isGameBlocked, blockGameFromTwitter, checkForUomi } = require('./simple_game_state');
```

3. **Make these 2 simple changes to your existing `processCommentLogic`**:

## Change 1: Add uomi detection (add this at the very beginning)

**ADD THIS as the FIRST thing in your processCommentLogic function:**
```javascript
// NEW: Check if this comment contains 'uomi' - ADD THIS FIRST
if (checkForUomi(comment.text)) {
    console.log('🏆 UOMI detected in comment! This user wins!');
    
    blockGameFromTwitter(comment.text, comment.id, comment.author.id);
    
    const winMessage = '🏆 Congratulations! You found the secret word! Please reply with your wallet address to receive your prize.';
    await this.twitterService.replyToComment(comment.id, winMessage);
    
    return; // Stop processing this comment
}
```

## Change 2: Replace your winners.txt check

**Find this line in your existing code:**
```javascript
if (fs.existsSync(winnersFilePath)) {
```

**Replace it with:**
```javascript
if (isGameBlocked()) {
```

## That's It!

Keep everything else exactly the same. Your existing logic for wallet detection, prize sending, etc. doesn't change at all.

## What This Does

- When someone tweets "uomi", it blocks the game for BOTH Twitter and Python chat
- The Python chat system immediately sees the block and stops accepting new queries
- Your existing wallet/prize logic keeps working exactly as before
