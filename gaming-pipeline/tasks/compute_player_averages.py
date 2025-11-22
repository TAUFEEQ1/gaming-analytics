import luigi

class ComputePlayerAveragesTask(luigi.Task):
    """
    A Luigi Task to compute average statistics per player.
    """
    def output(self):
        return luigi.LocalTarget('data/player_averages.csv')
    
    def input(self):
        return luigi.LocalTarget('data/onlineCasino.csv')

    def run(self):
        import pandas as pd
        
        # Read the input CSV file
        df = pd.read_csv(self.input().path)
        # the data is aggregated per round. 
        #  we know the money staked (money), gamers in a round (gamers)
        df['stake_per_player'] = df['money'] / df['gamers']
        #  we want the payout per player
        df['payout_per_player'] = df['peopleWin'] / df['gamers']
        #  pay ratio per player
        df['per_player_pay_ratio'] = df['payout_per_player'] / df['stake_per_player']
        
        # we are interested in the ID, stake per player, payout per player, pay ratio per player,time i.e timestamp
        player_df = df[['ID', 'stake_per_player', 'payout_per_player', 'per_player_pay_ratio', 'time']]
        # confirm the time is datetime 
        player_df['time'] = pd.to_datetime(player_df['time'])
        # Save the player averages to the output CSV file
        player_df.to_csv(self.output().path, index=False)

if __name__ == '__main__':
    luigi.run()