Don't push this to Git

I want to expand on this idea significantly. I want to make a  new Letterboxd. Letterboxd is prety bad right now. Onboarding takes ages, UX is bad, app is slow, there are no influencers or central figures that users can coalesce around, interactions with friends is clunky, it's hard to discover what other people like, and whose taste matches with me and whose does not. Thus, there is a lot of whitespace for improvement. 

I want to expand the current experience we have created so far. I want to offer it to my friends initally and then maybe even turn this into a production grade offering. Currently, we can import one's Letterboxd csv and go from there. However, (i) this is bad UX, it's too many steps to login into letterboxd, get your csv, download it, and upload to FeedMovie. We should just ask for the username and fetch their movie and friend list ourselves since they are public. (ii) lot of people don't have Letterboxd, and will be starting anew. Thus, we should have them pick and rank a set of popular movies in the card/swipe like fashion we use for our recommedations. We can also ask them which genres they like/dislike. 

This is the onboarding flow. 

Implement this for now. I think we should also create user profiles and such now since we are opening up to multiple people. If you think we need to migrate our database and such let me know and I can set that up as well.  

That said, after we integrate the onboarding and user flow, I want to make the experience more long-term such that user keep returning to build their movie library by ranking and reviewing new movies they're watching, connecting with friends, discovering new friends, and so on. I care about those things less right now. The core problem I want to solve first is really honing down the recommendations for new users and being able to suggest them a movie they would actually watch.