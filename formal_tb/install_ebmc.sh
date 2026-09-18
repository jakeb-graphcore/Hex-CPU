sudo xcode-select --install
new_tap_out=$(brew tap-new $USER/ebmc_tap | grep "Initialized empty Git repository") #Initialized empty Git repository in /usr/local/Homebrew/Library/Taps/reesjon9/homebrew-hmm2/.git/
tap_repo=$(echo "$new_tap_out" | sed "s/\(Initialized empty Git repository in \)\(.*\)\(.git\/\)/\2/")
cd "$tap_repo"
cd Formula
wget https://raw.githubusercontent.com/diffblue/hw-cbmc/main/Formula/ebmc@5.6.rb -O ebmc.rb
git add ebmc.rb
git commit -m "Add ebmc"
brew install "$USER/ebmc_tap/ebmc"
#ln -s /usr/local/Cellar/ebmc/5.6/usr/bin/ebmc ebmc
