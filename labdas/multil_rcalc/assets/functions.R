
myRcode <- function(number, bericht) {
  list(newvalue = number * 2, bericht = bericht, status = "alles goed")
}


# FUnction that assumes we are receiving the whole JSON data 
forestPrepare <- function(dataset, filtervar="", predictor="", useDataFilter=FALSE) {
  # Make sure the $Dataset part is read as a TIBBLE
  # dat <- dataset %>% as.tibble
  
  # Data klaarmaken voor de analyses
  dataset[dataset == "NA" | dataset == "MD" | dataset == "?"] <- NA
  
  # De volgende code moet gerund worden voorafgaand aan de analyses (maar na het filteren, als er ergens op gefilterd is).
  dat <- dataset %>%
    # change potential predictors to factors:
    mutate(target_language = as.factor(target_language),
           task_type = as.factor(task_type), 
           task_detailed = as.factor(task_detailed), 
           linguistic_property = as.factor(linguistic_property), 
           surface_overlap_author = as.factor(surface_overlap_author), 
           target_or_child_system = as.factor(target_or_child_system)) %>% 
    # only include test cases of CLI
    dplyr::filter(CLI_predicted == "yes") %>% 
    # compute average variance per sample 
    group_by(sample) %>% 
    mutate(g_var_avg = mean(g_var)) %>% 
    ungroup()
  
  # Extract the effect-size ($yi) and the sampling variance ($vi) as well as the include/skip list ($not.na) and the row name (dat1$short_cite)
  oData <- data.frame(
    observation = dat$observation,
    effectSize = dat$g_correct_sign,
    sampVar = dat$g_var,
    weight = 1 / dat$g_var
  )  
  # Provide this as PlotData for the output
  oPlotData <- jsonlite::toJSON(oData)
  
  
  # create variable that distinguishes different outcome measures (to be used in the vcalc function)
  dat$outcome <- paste(dat$linguistic_property_detailed, dat$task_detailed, dat$target_language, sep = "-")
  
  # At this point we need to know whether a predictor is being provided or not
  
  if (predictor == "") {
    # No predictor provided: using model1
    
    # create covariance matrices:
    V0 <- vcalc(g_var_avg, cluster = sample, type = outcome, grp1 = monolingual_group, grp2 = bilingual_group, w1 = n_L1, w2 = n_2L1, rho = 0, data = dat)
    
    V0.6 <- vcalc(g_var_avg, cluster = sample, type = outcome, grp1 = monolingual_group, grp2 = bilingual_group, w1 = n_L1, w2 = n_2L1, rho = 0.6, data = dat)
    
    V0.95 <- vcalc(g_var_avg, cluster = sample, type = outcome, grp1 = monolingual_group, grp2 = bilingual_group, w1 = n_L1, w2 = n_2L1, rho = 0.95, data = dat)
    
    
    # run models
    meta1a <- rma.mv(g_correct_sign, V0.6, data = dat, random = ~ 1|research_group/data_collection/observation)
    model1a <- conf_int(meta1a, vcov = "CR2")
    
    meta1b <- rma.mv(g_correct_sign, V0, data = dat, random = ~ 1|research_group/data_collection/observation)
    model1b <- conf_int(meta1b, vcov = "CR2")
    
    meta1c <- rma.mv(g_correct_sign, V0.95, data = dat, random = ~ 1|research_group/data_collection/observation)
    model1c <- conf_int(meta1c, vcov = "CR2")
    
    # Hele korte samenvatting van de analyse gebaseerd op het model zonder predictors (model 1): 
    #  Number of studies, number of datapoints, effect size, confidence interval. 
    #
    # Create a 'short summary'
    short_summary <- list(
      # Number of studies
      number_studies = length(unique(dat$short_cite)),
      # Number of datapoints
      number_data = nrow(dat),
      # effect size
      effect_size = model1a$beta,
      # lower bound confidence interval
      conf_lbound = model1a$CI_L,
      # upper bound confidence interval
      conf_ubound = model1a$CI_U
    )
    
    # Uitgebreide samenvatting van model 1 als de gebruiker geen predictors geselecteerd heeft
    extended_summary <- list(
      # The model call - but as a string
      model_call = capture.output(meta1a$call),
      # de informatie die hierin staat t/m Test for Heterogeneity - as a string
      summary = capture.output(summary(meta1a)),
      # de informatie die hierin staat, achter Estimate én achter SE moet (r = 0.60) komen te staan
      model1a = model1a,
      # Hieruit de estimates en SEs met "(r = 0.0)" erachter
      model1b = model1b,
      # Hieruit de estimates en SEs met "(r = 0.95)" erachter
      model1c = model1c
    )
    
    
  } else {
    # A predictor is provided: using model 2

    # Double check: filtervar may not equal predictor
    if (filtervar == predictor) {

        # Should generate an error message
        short_summary <- "ERROR"
        extended_summary <- "The [predictor] may not be equal to the [filtervar]"

    } else {

        # ------- DEBUG ----------------------
        print("Point #1")
        # ------------------------------------
    
        # Filter eerst op alleen de positieve effect sizes en bereken dan opnieuw de covariance matrices:
    
        dat2 <- dat %>% dplyr::filter(g_correct_sign >= 0)
    
        # ------- DEBUG ----------------------
        print("Point #2")
        # ------------------------------------
    
        # create variance-covariance matrices:
        V0b <- vcalc(g_var_avg, cluster = sample, type = outcome, grp1 = monolingual_group, grp2 = bilingual_group, w1 = n_L1, w2 = n_2L1, rho = 0, data = dat2)
        V0.6b <- vcalc(g_var_avg, cluster = sample, type = outcome, grp1 = monolingual_group, grp2 = bilingual_group, w1 = n_L1, w2 = n_2L1, rho = 0.6, data = dat2)
        V0.95b <- vcalc(g_var_avg, cluster = sample, type = outcome, grp1 = monolingual_group, grp2 = bilingual_group, w1 = n_L1, w2 = n_2L1, rho = 0.95, data = dat2)  
  
        # ------- DEBUG ----------------------
        print("Point #3a")
        # ------------------------------------

        # Add a column "predictor" to dat2
        dat2$predictor <- dat2[[predictor]]

        # issue #35.2 - determine whether mods = ~predictor should have something subtracted or not
        if (predictor == "mean_age_2L1") {
            # Do *NOT* subtract 1 from ~predictor in rma.mv
            
            # ------- DEBUG ----------------------
            print("Point #3b")
            # ------------------------------------

            # Hierna kunnen de modellen gerund worden, waarbij “predictor” de predictor is die de gebruiker geselecteerd heeft:
            meta2a <- rma.mv(g_correct_sign, V0.6b, data = dat2, mods = ~predictor, random = ~ 1|research_group/data_collection/observation)
            model2a <- conf_int(meta2a, vcov = "CR2")
    
            # ------- DEBUG ----------------------
            print("Point #3c")
            # ------------------------------------

            meta2b <- rma.mv(g_correct_sign, V0b, data = dat2, mods = ~predictor, random = ~ 1|research_group/data_collection/observation)
            model2b <- conf_int(meta2b, vcov = "CR2")
    
            meta2c <- rma.mv(g_correct_sign, V0.95b, data = dat2, mods = ~predictor, random = ~ 1|research_group/data_collection/observation)
            model2c <- conf_int(meta2c, vcov = "CR2")
        } else {
            # *DO* subtract 1 from ~predictor in rma.mv
            # ------- DEBUG ----------------------
            print("Point #3b")
            # ------------------------------------

            # Hierna kunnen de modellen gerund worden, waarbij “predictor” de predictor is die de gebruiker geselecteerd heeft:
            meta2a <- rma.mv(g_correct_sign, V0.6b, data = dat2, mods = ~predictor -1, random = ~ 1|research_group/data_collection/observation)
            model2a <- conf_int(meta2a, vcov = "CR2")
    
            # ------- DEBUG ----------------------
            print("Point #3c")
            # ------------------------------------

            meta2b <- rma.mv(g_correct_sign, V0b, data = dat2, mods = ~predictor -1, random = ~ 1|research_group/data_collection/observation)
            model2b <- conf_int(meta2b, vcov = "CR2")
    
            meta2c <- rma.mv(g_correct_sign, V0.95b, data = dat2, mods = ~predictor -1, random = ~ 1|research_group/data_collection/observation)
            model2c <- conf_int(meta2c, vcov = "CR2")
        }
    
    
        # ------- DEBUG ----------------------
        print("Point #4")
        # ------------------------------------
    
        # LET OP: als de gebruiker target_or_child_system heeft gekozen als variabele, 
        #   wordt naast target_or_child_system ook de predictor surface_overlap_author toegevoegd 
        #   én de interactie tussen deze twee variabelen:
        # issue #35: not 'filtervar' but 'predictor'
        if (predictor == "target_or_child") {
          meta2a <- rma.mv(g_correct_sign, V0.6b, data = dat2, mods =~target_or_child_system*surface_overlap_author -1, random = ~ 1|research_group/data_collection/observation)
          ## Warning: Rows with NAs omitted from model fitting.
          model2a <- conf_int(meta2a, vcov = "CR2")
      
          meta2b <- rma.mv(g_correct_sign, V0b, data = dat2, mods = ~target_or_child_system*surface_overlap_author -1, random = ~ 1|research_group/data_collection/observation)
          ## Warning: Rows with NAs omitted from model fitting.
          model2b <- conf_int(meta2b, vcov = "CR2")
      
          meta2c <- rma.mv(g_correct_sign, V0.95b, data = dat2, mods = ~target_or_child_system*surface_overlap_author -1, random = ~ 1|research_group/data_collection/observation)
          ## Warning: Rows with NAs omitted from model fitting.
          model2c <- conf_int(meta2c, vcov = "CR2")
      
        }
    
        # Hele korte samenvatting van de analyse gebaseerd op het model met predictors (model 2): 
        #  Number of studies, number of datapoints, effect size, confidence interval. 
        #
        # Create a 'short summary'
        short_summary <- list(
          # Number of studies
          number_studies = length(unique(dat2$short_cite)),
          # Number of datapoints
          number_data = nrow(dat2),
          # effect size
          effect_size = model2a$beta,
          # lower bound confidence interval
          conf_lbound = model2a$CI_L,
          # upper bound confidence interval
          conf_ubound = model2a$CI_U
        )
    
        # ------- DEBUG ----------------------
        print("Point: post short_summary")
        # ------------------------------------
    
        # Uitgebreide samenvatting van model 2 als de gebruiker wel predictors geselecteerd heeft
        extended_summary <- list(
          # The model call - but as a string
          model_call = capture.output(meta2a$call),
          # de informatie die hierin staat t/m Test for Heterogeneity - as a string
          summary = capture.output(summary(meta2a)),
          # de informatie die hierin staat, achter Estimate én achter SE moet (r = 0.60) komen te staan
          model2a = model2a,
          # Hieruit de estimates en SEs met "(r = 0.0)" erachter
          model2b = model2b,
          # Hieruit de estimates en SEs met "(r = 0.95)" erachter
          model12c = model2c
        )

        # ------- DEBUG ----------------------
        print("Point: post extended_summary")
        # ------------------------------------
    
    }
    
  }
  
  # Combine the output: plotdata, short_summary, extended_summary
  l <- list(plotdata = oPlotData, 
            short = short_summary,
            extended = extended_summary)
  oBack <- jsonlite::toJSON(l)
    
  # Return what we found
  return ( oBack )
}

# ----------------------------------------------------------------------------
# The main entry point for all purposes
#
# Action depends on 'calling':
# - if empty: just call forestPrepare()
# - if 'debug' or 'test': return message 'alles goed'
# - otherwise: signal that the command is not known
# ----------------------------------------------------------------------------
multilingEntry <- function(dataset_raw, calling="", filtervar="", predictor="") {
    logdebug("Start multilingEntry", logger = 'runtime')

    # This is the main entry point
    if (calling == "" | calling == "forestprepare") {
        dataset <- as.data.frame(dataset_raw)
        # Call forest prepare
        oBack <- forestPrepare(dataset, filtervar, predictor)

        return( oBack )
    } else if (calling == "usedatafilter") {
        dataset <- as.data.frame(dataset_raw)
        # Call forest prepare
        oBack <- forestPrepare(dataset, filtervar, predictor, useDataFilter=TRUE)

        return( oBack )
    } else if (calling == "debug" | calling == "test") {
        list(bericht = calling, status = "alles goed")
    } else {
        list(bericht = calling, status = "Dit commando is onbekend")
    }
}