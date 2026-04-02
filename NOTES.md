# Tasks
## 1. Bug Finding and Fixing
I first started by watching the video, where I noticed the constant camera movement even though there is no visible movement. 

Then I checked the code to understand how it works, this is where I figured that the issue must be with the deadzone detection.

Onwards, I saw that the deadzone comparison is 0 instead of the actual deadzone threshold (dz_half_x, dz_half_y). 

Once I fixed that and verified that it now works, I then write tests to future-proof my code should there be any need for changes.

Comments: Noticed that the y-axis of crop will never move, was pretty sure that's intended, assuming that the video height and video width is the cropped variant and not the original ratio.

PS: Checked the json data and figured this to indeed be the case

## 2. Feature Implementation
I first started my reading the docString, and then got AI to assist me in writing test cases, which I then verified.

Then, I started to implement the features, making sure I gradually pass all test cases.

Comments: In terms of alternating short frames, I wasn't sure on how to handle it. I was thinking either splitting it equally among all speakers, or just focus on one speaker. The current implementation is based on the latter, but I believe the former would be better for real use cases